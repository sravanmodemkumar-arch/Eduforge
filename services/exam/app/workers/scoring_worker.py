"""
SQS-based scoring worker.

Polls the scoring queue for jobs and processes them:
  1. score_attempt  -> compute score for a single attempt
  2. compute_ranks  -> recompute rankings for an entire test
  3. After scoring, triggers rank recomputation and notification

Can be run as a standalone process:
    python -m app.workers.scoring_worker
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

import boto3
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)
settings = get_settings()


async def process_message(session_factory: async_sessionmaker[AsyncSession], body: dict) -> None:
    """Process a single SQS message."""
    msg_type = body.get("type")
    logger.info("Processing message: type=%s", msg_type)

    async with session_factory() as db:
        scoring = ScoringService(db)

        try:
            if msg_type == "score_attempt":
                attempt_id = uuid.UUID(body["attempt_id"])
                test_id = uuid.UUID(body["test_id"])

                # Score the individual attempt
                result = await scoring.score_attempt(attempt_id)
                logger.info("Scored attempt %s -> score=%.2f", attempt_id, result.total_score)

                # Generate HTML result card
                await scoring.generate_result_html(result.id)

                # Recompute ranks for the test
                await scoring.compute_ranks(test_id)
                logger.info("Ranks recomputed for test %s", test_id)

                await db.commit()

                # Notify via SQS
                await _send_notification(
                    student_id=str(result.student_id),
                    test_id=str(test_id),
                    result_id=str(result.id),
                    score=result.total_score,
                    percentage=result.percentage,
                )

            elif msg_type == "compute_ranks":
                test_id = uuid.UUID(body["test_id"])
                await scoring.compute_ranks(test_id)
                await db.commit()
                logger.info("Ranks recomputed for test %s", test_id)

            else:
                logger.warning("Unknown message type: %s", msg_type)

        except Exception:
            await db.rollback()
            logger.exception("Failed to process message: %s", body)
            raise


async def _send_notification(
    student_id: str,
    test_id: str,
    result_id: str,
    score: float,
    percentage: float,
) -> None:
    """Send a notification message to the notification service via SQS."""
    if not settings.SQS_NOTIFICATION_QUEUE_URL:
        return

    try:
        sqs = boto3.client(
            "sqs",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        sqs.send_message(
            QueueUrl=settings.SQS_NOTIFICATION_QUEUE_URL,
            MessageBody=json.dumps({
                "type": "exam_result_ready",
                "student_id": student_id,
                "test_id": test_id,
                "result_id": result_id,
                "score": score,
                "percentage": percentage,
            }),
        )
    except Exception:
        logger.exception("Failed to send notification for result %s", result_id)


async def poll_queue(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Long-poll SQS and process messages continuously."""
    if not settings.SQS_QUEUE_URL:
        logger.error("SQS_QUEUE_URL not configured. Exiting worker.")
        return

    sqs = boto3.client(
        "sqs",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )

    logger.info("Scoring worker started. Polling %s", settings.SQS_QUEUE_URL)

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=settings.SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                VisibilityTimeout=120,
            )

            messages = response.get("Messages", [])
            for msg in messages:
                body = json.loads(msg["Body"])
                try:
                    await process_message(session_factory, body)
                    # Delete message on success
                    sqs.delete_message(
                        QueueUrl=settings.SQS_QUEUE_URL,
                        ReceiptHandle=msg["ReceiptHandle"],
                    )
                except Exception:
                    logger.exception("Message processing failed, will retry: %s", msg["MessageId"])

        except Exception:
            logger.exception("Error polling SQS queue")
            await asyncio.sleep(5)


def main() -> None:
    """Entry point for running the scoring worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=2,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    asyncio.run(poll_queue(session_factory))


if __name__ == "__main__":
    main()
