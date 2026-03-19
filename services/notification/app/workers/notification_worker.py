"""
SQS-based notification worker.

Continuously polls an SQS queue for notification jobs, deserialises them,
and dispatches through the NotificationService.  Designed to run as a
long-lived process (e.g. in an ECS task or a standalone container).

Usage:
    python -m app.workers.notification_worker
"""

import asyncio
import json
import logging
import signal
import sys
from typing import Any

import boto3
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.exceptions import NotificationServiceError
from app.schemas.notification import NotificationSendRequest
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

settings = get_settings()

# ── Database engine (async) ──────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DB_ECHO,
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── SQS client ──────────────────────────────────────────────────────────────
sqs = boto3.client("sqs", region_name=settings.AWS_REGION)


class NotificationWorker:
    """Polls SQS and processes notification messages."""

    def __init__(self) -> None:
        self._running = True
        self.queue_url = settings.SQS_QUEUE_URL
        self.max_messages = settings.SQS_MAX_MESSAGES
        self.wait_time = settings.SQS_WAIT_TIME_SECONDS
        self.visibility_timeout = settings.SQS_VISIBILITY_TIMEOUT

    def stop(self) -> None:
        """Signal the worker to stop gracefully."""
        logger.info("Shutdown signal received – finishing current batch…")
        self._running = False

    async def run(self) -> None:
        """Main polling loop."""
        logger.info("Notification worker started – polling %s", self.queue_url)

        while self._running:
            try:
                messages = await asyncio.to_thread(self._receive_messages)
                if not messages:
                    continue

                for message in messages:
                    await self._process_message(message)

            except Exception:
                logger.exception("Unexpected error in polling loop")
                await asyncio.sleep(5)

        logger.info("Notification worker stopped.")

    def _receive_messages(self) -> list[dict[str, Any]]:
        """Long-poll SQS for messages (runs in a thread)."""
        response = sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=self.max_messages,
            WaitTimeSeconds=self.wait_time,
            VisibilityTimeout=self.visibility_timeout,
            MessageAttributeNames=["All"],
        )
        return response.get("Messages", [])

    async def _process_message(self, message: dict[str, Any]) -> None:
        """Parse, dispatch, and acknowledge a single SQS message."""
        receipt_handle = message["ReceiptHandle"]
        message_id = message.get("MessageId", "unknown")

        try:
            body = json.loads(message["Body"])
            request = NotificationSendRequest(**body)

            async with AsyncSessionLocal() as session:
                service = NotificationService(session)
                result = await service.send(request)
                logger.info(
                    "Processed message %s → notification %s [%s]",
                    message_id,
                    result.id,
                    result.status,
                )

            # Delete message from queue on success
            await asyncio.to_thread(
                sqs.delete_message,
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )

        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.error(
                "Invalid message payload %s: %s – deleting poisoned message",
                message_id,
                exc,
            )
            # Remove malformed messages to prevent infinite reprocessing
            await asyncio.to_thread(
                sqs.delete_message,
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )

        except NotificationServiceError as exc:
            logger.error(
                "Service error processing message %s: %s – "
                "message will return to queue after visibility timeout",
                message_id,
                exc,
            )

        except Exception:
            logger.exception(
                "Unexpected error processing message %s – "
                "message will return to queue after visibility timeout",
                message_id,
            )


def main() -> None:
    """Entry-point for the worker process."""
    worker = NotificationWorker()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Graceful shutdown on SIGINT / SIGTERM
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, worker.stop)

    try:
        loop.run_until_complete(worker.run())
    finally:
        loop.run_until_complete(engine.dispose())
        loop.close()


if __name__ == "__main__":
    main()
