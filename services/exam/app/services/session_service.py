from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timezone

import boto3
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import (
    ActiveSessionExistsError,
    SessionAlreadySubmittedError,
    SessionExpiredError,
    SessionNotFoundError,
    TestNotActiveError,
    TestNotFoundError,
    TimeWindowExceededError,
)
from app.models.attempt import Attempt, SubmitSource
from app.models.exam_session import ExamSession, SessionStatus
from app.models.test import Test

settings = get_settings()


class SessionService:
    """Business logic for exam sessions -- the core IndexedDB flow."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Start session (Lambda call #1) ───────────────────────────────────
    async def start_session(
        self,
        student_id: uuid.UUID,
        institution_id: uuid.UUID,
        test_id: uuid.UUID,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
    ) -> dict:
        # 1. Validate test exists and is active
        result = await self._db.execute(select(Test).where(Test.id == test_id))
        test = result.scalar_one_or_none()
        if not test:
            raise TestNotFoundError(str(test_id))

        if not test.is_published:
            raise TestNotActiveError(str(test_id))

        now = datetime.now(timezone.utc)
        if test.schedule_start and now < test.schedule_start:
            raise TestNotActiveError(str(test_id))
        if test.schedule_end and now > test.schedule_end:
            raise TestNotActiveError(str(test_id))

        # 2. Check no existing active session for this student + test
        existing = await self._db.execute(
            select(ExamSession).where(
                and_(
                    ExamSession.student_id == student_id,
                    ExamSession.test_id == test_id,
                    ExamSession.status == SessionStatus.ACTIVE,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ActiveSessionExistsError()

        # 3. Create session with random salt for encryption key derivation
        salt = secrets.token_hex(32)
        duration_seconds = test.duration_minutes * 60
        started_at = now

        session = ExamSession(
            test_id=test_id,
            student_id=student_id,
            institution_id=institution_id,
            salt=salt,
            started_at=started_at,
            duration_seconds=duration_seconds,
            status=SessionStatus.ACTIVE,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
        )
        self._db.add(session)
        await self._db.flush()
        await self._db.refresh(session)

        # 4. Build CDN URL for encrypted questions JSON
        test_r2_url = f"{settings.CDN_BASE_URL}/{test.r2_questions_key}"

        return {
            "session_id": session.id,
            "test_r2_url": test_r2_url,
            "salt": salt,
            "duration_seconds": duration_seconds,
            "started_at": started_at,
        }

    # ── Submit session (Lambda call #2) ──────────────────────────────────
    async def submit_session(
        self,
        session_id: uuid.UUID,
        student_id: uuid.UUID,
        answers: dict[str, str],
        time_taken_seconds: int,
        submit_source: str,
    ) -> dict:
        # 1. Load session
        result = await self._db.execute(
            select(ExamSession).where(
                and_(
                    ExamSession.id == session_id,
                    ExamSession.student_id == student_id,
                )
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise SessionNotFoundError(str(session_id))

        # 2. Validate not already submitted
        if session.status == SessionStatus.SUBMITTED:
            raise SessionAlreadySubmittedError(str(session_id))

        if session.status == SessionStatus.EXPIRED:
            raise SessionExpiredError(str(session_id))

        # 3. Validate within time window (duration + grace period)
        now = datetime.now(timezone.utc)
        deadline = session.started_at.replace(tzinfo=timezone.utc) if session.started_at.tzinfo is None else session.started_at
        from datetime import timedelta
        deadline = deadline + timedelta(seconds=session.duration_seconds + settings.SESSION_GRACE_PERIOD_SECONDS)
        if now > deadline:
            session.status = SessionStatus.EXPIRED
            await self._db.flush()
            raise TimeWindowExceededError(str(session_id))

        # 4. Mark session as submitted
        session.status = SessionStatus.SUBMITTED
        session.answers_received = True

        # 5. Create attempt record
        attempt = Attempt(
            session_id=session.id,
            test_id=session.test_id,
            student_id=student_id,
            institution_id=session.institution_id,
            answers=answers,
            time_taken_seconds=time_taken_seconds,
            submit_source=SubmitSource(submit_source),
        )
        self._db.add(attempt)
        await self._db.flush()
        await self._db.refresh(attempt)

        # 6. Send SQS message for async scoring
        await self._send_scoring_message(attempt.id, session.test_id)

        return {
            "session_id": session.id,
            "status": session.status.value,
            "submitted_at": attempt.submitted_at,
            "message": "Answers submitted successfully. Scoring in progress.",
        }

    # ── Recover session (crash recovery) ─────────────────────────────────
    async def recover_session(
        self,
        session_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> dict:
        result = await self._db.execute(
            select(ExamSession).where(
                and_(
                    ExamSession.id == session_id,
                    ExamSession.student_id == student_id,
                )
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise SessionNotFoundError(str(session_id))

        now = datetime.now(timezone.utc)
        started = session.started_at.replace(tzinfo=timezone.utc) if session.started_at.tzinfo is None else session.started_at
        elapsed = (now - started).total_seconds()
        time_remaining = max(0, session.duration_seconds - int(elapsed))

        # If time has run out and session is still active, mark as expired
        if time_remaining == 0 and session.status == SessionStatus.ACTIVE:
            session.status = SessionStatus.EXPIRED
            await self._db.flush()

        return {
            "session_id": session.id,
            "time_remaining": time_remaining,
            "status": session.status.value,
            "started_at": session.started_at,
        }

    # ── Internal: send SQS scoring job ───────────────────────────────────
    async def _send_scoring_message(self, attempt_id: uuid.UUID, test_id: uuid.UUID) -> None:
        if not settings.SQS_QUEUE_URL:
            return  # Skip in local dev

        try:
            sqs = boto3.client(
                "sqs",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            )
            sqs.send_message(
                QueueUrl=settings.SQS_QUEUE_URL,
                MessageBody=json.dumps({
                    "type": "score_attempt",
                    "attempt_id": str(attempt_id),
                    "test_id": str(test_id),
                }),
                MessageGroupId=str(test_id),
            )
        except Exception:
            # Log but don't fail the submission -- scoring can be retried
            pass
