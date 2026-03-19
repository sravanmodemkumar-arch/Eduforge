"""Service layer for AI-powered doubt resolution."""

from __future__ import annotations

import logging
from typing import Optional, Sequence
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.exceptions import AIProcessingError, DoubtNotFoundError
from app.models.doubt import Doubt
from app.schemas.doubt import DoubtCreate, DoubtResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert educational tutor on the EduForge platform. "
    "When a student asks a question, respond with a clear, structured explanation. "
    "Break complex problems into manageable steps. "
    "Use examples and analogies appropriate to the student's level. "
    "Always encourage the student and highlight the key concept being tested. "
    "If the question involves a calculation, show the full working. "
    "Format your response using Markdown for readability."
)

engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


class DoubtService:
    """Handles creation, retrieval and AI resolution of student doubts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Commands ───────────────────────────────────────────────────────

    async def create_doubt(self, payload: DoubtCreate) -> DoubtResponse:
        """Persist a new doubt, resolve it via OpenAI, and return the result."""
        doubt = Doubt(
            student_id=payload.student_id,
            institution_id=payload.institution_id,
            subject=payload.subject,
            question_text=payload.question_text,
            image_r2_key=payload.image_r2_key,
            status="processing",
        )
        self._session.add(doubt)
        await self._session.flush()

        try:
            ai_response, model_used, tokens_used = await self._resolve_with_ai(
                payload.question_text, payload.subject
            )
            doubt.ai_response = ai_response
            doubt.model_used = model_used
            doubt.tokens_used = tokens_used
            doubt.status = "resolved"
        except Exception:
            logger.exception("AI resolution failed for doubt %s", doubt.id)
            doubt.status = "failed"
            await self._session.commit()
            raise AIProcessingError(doubt_id=str(doubt.id))

        await self._session.commit()
        await self._session.refresh(doubt)
        return DoubtResponse.model_validate(doubt)

    # ── Queries ────────────────────────────────────────────────────────

    async def get_doubt_by_id(self, doubt_id: UUID) -> DoubtResponse | None:
        """Return a single doubt or ``None``."""
        result = await self._session.execute(
            select(Doubt).where(Doubt.id == doubt_id)
        )
        doubt = result.scalar_one_or_none()
        if doubt is None:
            return None
        return DoubtResponse.model_validate(doubt)

    async def list_doubts(
        self,
        *,
        student_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        subject: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[DoubtResponse], int]:
        """Return a filtered, paginated list of doubts."""
        query = select(Doubt)
        count_query = select(func.count()).select_from(Doubt)

        if student_id is not None:
            query = query.where(Doubt.student_id == student_id)
            count_query = count_query.where(Doubt.student_id == student_id)
        if institution_id is not None:
            query = query.where(Doubt.institution_id == institution_id)
            count_query = count_query.where(Doubt.institution_id == institution_id)
        if subject is not None:
            query = query.where(Doubt.subject == subject)
            count_query = count_query.where(Doubt.subject == subject)
        if status is not None:
            query = query.where(Doubt.status == status)
            count_query = count_query.where(Doubt.status == status)

        total = (await self._session.execute(count_query)).scalar_one()

        query = (
            query.order_by(Doubt.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        doubts = result.scalars().all()

        return [DoubtResponse.model_validate(d) for d in doubts], total

    # ── Internal ───────────────────────────────────────────────────────

    @staticmethod
    async def _resolve_with_ai(
        question: str, subject: str
    ) -> tuple[str, str, int]:
        """Call OpenAI and return (response_text, model, tokens_used)."""
        user_content = f"Subject: {subject}\n\nQuestion: {question}"

        completion = await openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature,
        )

        choice = completion.choices[0]
        tokens = completion.usage.total_tokens if completion.usage else 0
        return choice.message.content or "", completion.model, tokens


async def get_doubt_service() -> DoubtService:
    """FastAPI dependency that yields a ``DoubtService`` per request."""
    async with async_session() as session:
        yield DoubtService(session)
