from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Result(Base):
    __tablename__ = "results"
    __table_args__ = {"schema": "exam"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("exam.attempts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exam.tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    institution_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)

    # ── Scores ───────────────────────────────────────────────────────────
    total_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    incorrect_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unanswered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Ranking ──────────────────────────────────────────────────────────
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percentile: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Section-level breakdown ──────────────────────────────────────────
    section_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Pre-rendered result HTML in R2 ───────────────────────────────────
    result_r2_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
