"""Service layer for AI-powered study recommendations."""

from __future__ import annotations

import json
import logging
from typing import Optional
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.doubt import Doubt
from app.schemas.doubt import (
    StudyPlanItem,
    StudyPlanResponse,
    WeakTopic,
    WeakTopicsResponse,
)

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

STUDY_PLAN_SYSTEM_PROMPT = (
    "You are an expert educational advisor on the EduForge platform. "
    "Given a student's doubt history for a subject, generate a personalised "
    "study plan as a JSON array. Each item must have: topic (string), "
    "priority ('high'|'medium'|'low'), estimated_hours (number), "
    "resources (string array of suggested resource titles), and "
    "rationale (string explaining why this topic is included). "
    "Also include a 'summary' key with a brief overall recommendation. "
    "Return valid JSON with keys 'items' and 'summary'. No markdown fences."
)

WEAK_TOPICS_SYSTEM_PROMPT = (
    "You are an expert educational analyst on the EduForge platform. "
    "Given a student's doubt history, identify the topics where the student "
    "is weakest. Return a JSON array under key 'topics'. Each item must have: "
    "topic (string), subject (string), doubt_count (integer), "
    "confidence_score (float 0-1 indicating weakness severity, 1 = very weak), "
    "and suggestion (string with an actionable recommendation). "
    "Return valid JSON only. No markdown fences."
)


class RecommendationService:
    """Generates study plans and weak-topic analyses."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def generate_study_plan(
        self, student_id: UUID, subject: str
    ) -> StudyPlanResponse:
        """Build a study plan from the student's doubt history."""
        history = await self._fetch_doubt_history(student_id, subject)
        history_text = self._format_history(history)

        user_content = (
            f"Student ID: {student_id}\n"
            f"Subject: {subject}\n\n"
            f"Doubt history:\n{history_text}"
        )

        raw = await self._call_openai(STUDY_PLAN_SYSTEM_PROMPT, user_content)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse study-plan JSON: %s", raw[:500])
            data = {"items": [], "summary": "Unable to generate plan at this time."}

        items = [StudyPlanItem(**item) for item in data.get("items", [])]
        summary = data.get("summary", "")

        return StudyPlanResponse(
            student_id=student_id,
            subject=subject,
            items=items,
            summary=summary,
        )

    async def identify_weak_topics(
        self, student_id: UUID, subject: Optional[str] = None
    ) -> WeakTopicsResponse:
        """Return topics the student struggles with, ranked by severity."""
        history = await self._fetch_doubt_history(student_id, subject)
        history_text = self._format_history(history)

        user_content = (
            f"Student ID: {student_id}\n\n"
            f"Doubt history:\n{history_text}"
        )

        raw = await self._call_openai(WEAK_TOPICS_SYSTEM_PROMPT, user_content)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Failed to parse weak-topics JSON: %s", raw[:500])
            data = {"topics": []}

        topics = [WeakTopic(**t) for t in data.get("topics", [])]
        return WeakTopicsResponse(student_id=student_id, topics=topics)

    # ── Internal helpers ───────────────────────────────────────────────

    async def _fetch_doubt_history(
        self, student_id: UUID, subject: Optional[str] = None
    ) -> list[Doubt]:
        """Retrieve resolved doubts for the student, optionally filtered by subject."""
        query = (
            select(Doubt)
            .where(Doubt.student_id == student_id, Doubt.status == "resolved")
            .order_by(Doubt.created_at.desc())
            .limit(100)
        )
        if subject:
            query = query.where(Doubt.subject == subject)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    def _format_history(doubts: list[Doubt]) -> str:
        """Convert doubts into a compact textual summary for the LLM."""
        if not doubts:
            return "No previous doubts recorded."
        lines: list[str] = []
        for d in doubts:
            lines.append(
                f"- [{d.subject}] {d.question_text[:200]}"
            )
        return "\n".join(lines)

    @staticmethod
    async def _call_openai(system_prompt: str, user_content: str) -> str:
        """Send a chat completion request and return the response text."""
        completion = await openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature,
        )
        return completion.choices[0].message.content or ""


async def get_recommendation_service() -> RecommendationService:
    """FastAPI dependency that yields a ``RecommendationService`` per request."""
    async with async_session() as session:
        yield RecommendationService(session)
