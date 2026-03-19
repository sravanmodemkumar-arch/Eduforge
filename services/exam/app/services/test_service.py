from __future__ import annotations

import json
import uuid

import boto3
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import TestNotFoundError
from app.models.question import Question
from app.models.test import Test, TestType
from app.schemas.test import TestCreate

settings = get_settings()


class TestService:
    """Business logic for test management."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Create test ──────────────────────────────────────────────────────
    async def create_test(self, data: TestCreate, created_by: uuid.UUID) -> Test:
        test = Test(
            institution_id=data.institution_id,
            title=data.title,
            description=data.description,
            test_type=TestType(data.test_type),
            duration_minutes=data.duration_minutes,
            total_marks=data.total_marks,
            negative_marking=data.negative_marking,
            question_ids=data.question_ids,
            schedule_start=data.schedule_start,
            schedule_end=data.schedule_end,
            settings=data.settings,
            created_by=created_by,
        )
        self._db.add(test)
        await self._db.flush()
        await self._db.refresh(test)
        return test

    # ── Publish test ─────────────────────────────────────────────────────
    async def publish_test(self, test_id: uuid.UUID) -> Test:
        """Generates questions JSON, uploads to R2 for CDN serving, marks as published."""
        result = await self._db.execute(select(Test).where(Test.id == test_id))
        test = result.scalar_one_or_none()
        if not test:
            raise TestNotFoundError(str(test_id))

        # Build questions payload for CDN (excludes correct answers)
        questions_payload = await self._build_questions_json(test)

        # Upload to R2
        r2_key = f"tests/{test.institution_id}/{test.id}/questions.json"
        await self._upload_to_r2(r2_key, json.dumps(questions_payload, ensure_ascii=False))

        # Update test record
        test.r2_questions_key = r2_key
        test.is_published = True

        # Compute total marks from questions
        if test.question_ids:
            q_result = await self._db.execute(
                select(Question).where(Question.id.in_(test.question_ids))
            )
            questions = list(q_result.scalars().all())
            test.total_marks = sum(q.marks for q in questions)

        await self._db.flush()
        await self._db.refresh(test)
        return test

    # ── Build questions JSON for CDN (no answers!) ───────────────────────
    async def _build_questions_json(self, test: Test) -> dict:
        if not test.question_ids:
            return {"test_id": str(test.id), "questions": []}

        result = await self._db.execute(
            select(Question).where(Question.id.in_(test.question_ids))
        )
        questions = list(result.scalars().all())

        # Build a lookup for ordering
        id_order = {qid: idx for idx, qid in enumerate(test.question_ids)}
        questions.sort(key=lambda q: id_order.get(q.id, 0))

        questions_data = []
        for q in questions:
            questions_data.append({
                "id": str(q.id),
                "subject": q.subject,
                "topic": q.topic,
                "difficulty": q.difficulty.value,
                "question_text_en": q.question_text_en,
                "question_text_hi": q.question_text_hi,
                "options": q.options,
                "marks": q.marks,
                "negative_marks": q.negative_marks,
                # NOTE: correct_option_id is intentionally EXCLUDED
                # The browser never knows the correct answer during the exam
            })

        return {
            "test_id": str(test.id),
            "title": test.title,
            "duration_minutes": test.duration_minutes,
            "negative_marking": test.negative_marking,
            "total_questions": len(questions_data),
            "questions": questions_data,
        }

    # ── Upload to R2 (S3-compatible) ─────────────────────────────────────
    async def _upload_to_r2(self, key: str, body: str) -> None:
        if not settings.R2_ENDPOINT_URL:
            return  # Skip in local dev

        s3 = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name=settings.R2_REGION,
        )
        s3.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
            CacheControl="public, max-age=31536000, immutable",
        )
