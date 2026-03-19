from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import boto3
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import ResultNotFoundError
from app.models.attempt import Attempt
from app.models.question import Question
from app.models.result import Result
from app.models.test import Test

settings = get_settings()

# Jinja2 environment for result HTML rendering
_jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html"]),
)


class ScoringService:
    """Scores exam attempts and computes rankings."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Score a single attempt ───────────────────────────────────────────
    async def score_attempt(self, attempt_id: uuid.UUID) -> Result:
        # 1. Load attempt
        result = await self._db.execute(select(Attempt).where(Attempt.id == attempt_id))
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise ValueError(f"Attempt {attempt_id} not found")

        # 2. Load test
        test_result = await self._db.execute(select(Test).where(Test.id == attempt.test_id))
        test = test_result.scalar_one_or_none()
        if not test:
            raise ValueError(f"Test {attempt.test_id} not found")

        # 3. Load all questions for this test
        if test.question_ids:
            q_result = await self._db.execute(
                select(Question).where(Question.id.in_(test.question_ids))
            )
            questions = {str(q.id): q for q in q_result.scalars().all()}
        else:
            questions = {}

        # 4. Score each answer
        student_answers: dict = attempt.answers or {}
        total_score = 0.0
        max_score = 0.0
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        section_scores: dict[str, dict] = {}

        for q_id_str, question in questions.items():
            max_score += question.marks

            # Track per-subject section scores
            section = question.subject
            if section not in section_scores:
                section_scores[section] = {
                    "correct": 0,
                    "incorrect": 0,
                    "unanswered": 0,
                    "score": 0.0,
                    "max_score": 0.0,
                }
            section_scores[section]["max_score"] += question.marks

            student_answer = student_answers.get(q_id_str)
            if student_answer is None:
                unanswered_count += 1
                section_scores[section]["unanswered"] += 1
            elif student_answer == question.correct_option_id:
                correct_count += 1
                total_score += question.marks
                section_scores[section]["correct"] += 1
                section_scores[section]["score"] += question.marks
            else:
                incorrect_count += 1
                if test.negative_marking:
                    total_score -= question.negative_marks
                    section_scores[section]["score"] -= question.negative_marks
                section_scores[section]["incorrect"] += 1

        percentage = (total_score / max_score * 100) if max_score > 0 else 0.0

        # 5. Check for existing result (idempotency)
        existing = await self._db.execute(
            select(Result).where(Result.attempt_id == attempt_id)
        )
        existing_result = existing.scalar_one_or_none()

        if existing_result:
            existing_result.total_score = total_score
            existing_result.max_score = max_score
            existing_result.correct_count = correct_count
            existing_result.incorrect_count = incorrect_count
            existing_result.unanswered_count = unanswered_count
            existing_result.percentage = round(percentage, 2)
            existing_result.section_scores = section_scores
            existing_result.computed_at = datetime.now(timezone.utc)
            await self._db.flush()
            await self._db.refresh(existing_result)
            return existing_result

        # 6. Create result record
        exam_result = Result(
            attempt_id=attempt.id,
            test_id=attempt.test_id,
            student_id=attempt.student_id,
            institution_id=attempt.institution_id,
            total_score=total_score,
            max_score=max_score,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            unanswered_count=unanswered_count,
            percentage=round(percentage, 2),
            section_scores=section_scores,
        )
        self._db.add(exam_result)
        await self._db.flush()
        await self._db.refresh(exam_result)
        return exam_result

    # ── Compute ranks for all participants in a test ─────────────────────
    async def compute_ranks(self, test_id: uuid.UUID) -> None:
        result = await self._db.execute(
            select(Result)
            .where(Result.test_id == test_id)
            .order_by(Result.total_score.desc())
        )
        results = list(result.scalars().all())
        total_participants = len(results)

        if total_participants == 0:
            return

        for rank_idx, res in enumerate(results, start=1):
            res.rank = rank_idx
            res.total_participants = total_participants
            # Percentile: % of students scoring below this student
            res.percentile = round(
                ((total_participants - rank_idx) / total_participants) * 100, 2
            )

        await self._db.flush()

    # ── Generate result HTML and upload to R2 ────────────────────────────
    async def generate_result_html(self, result_id: uuid.UUID) -> str | None:
        res_query = await self._db.execute(select(Result).where(Result.id == result_id))
        exam_result = res_query.scalar_one_or_none()
        if not exam_result:
            raise ResultNotFoundError(f"Result {result_id} not found")

        # Load test title
        test_query = await self._db.execute(select(Test).where(Test.id == exam_result.test_id))
        test = test_query.scalar_one_or_none()
        test_title = test.title if test else "Unknown Test"

        try:
            template = _jinja_env.get_template("result.html")
        except Exception:
            # Template not available -- skip HTML generation
            return None

        html_content = template.render(
            result=exam_result,
            test_title=test_title,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Upload to R2
        r2_key = f"results/{exam_result.test_id}/{exam_result.student_id}/{result_id}.html"

        if settings.R2_ENDPOINT_URL:
            try:
                s3 = boto3.client(
                    "s3",
                    endpoint_url=settings.R2_ENDPOINT_URL,
                    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                    region_name=settings.R2_REGION,
                )
                s3.put_object(
                    Bucket=settings.R2_BUCKET_NAME,
                    Key=r2_key,
                    Body=html_content.encode("utf-8"),
                    ContentType="text/html",
                )
            except Exception:
                return None

        exam_result.result_r2_key = r2_key
        await self._db.flush()

        return r2_key
