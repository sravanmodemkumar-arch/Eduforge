from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    DateTime,
    Enum,
    Float,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DifficultyLevel(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class QuestionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = {"schema": "exam"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)

    # ── Classification ───────────────────────────────────────────────────
    subject: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level", schema="exam"),
        nullable=False,
        default=DifficultyLevel.MEDIUM,
        index=True,
    )

    # ── Bilingual content ────────────────────────────────────────────────
    question_text_en: Mapped[str] = mapped_column(Text, nullable=False)
    question_text_hi: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Options (JSONB list of {id, text_en, text_hi}) ───────────────────
    options: Mapped[dict] = mapped_column(JSONB, nullable=False)
    correct_option_id: Mapped[str] = mapped_column(String(8), nullable=False)

    # ── Explanations ─────────────────────────────────────────────────────
    explanation_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_hi: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Scoring ──────────────────────────────────────────────────────────
    marks: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    negative_marks: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Workflow ─────────────────────────────────────────────────────────
    status: Mapped[QuestionStatus] = mapped_column(
        Enum(QuestionStatus, name="question_status", schema="exam"),
        nullable=False,
        default=QuestionStatus.DRAFT,
        index=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    # ── Tags ─────────────────────────────────────────────────────────────
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
