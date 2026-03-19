from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TestType(str, enum.Enum):
    PRACTICE = "PRACTICE"
    MOCK = "MOCK"
    LIVE = "LIVE"


class Test(Base):
    __tablename__ = "tests"
    __table_args__ = {"schema": "exam"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)

    # ── Details ──────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_type: Mapped[TestType] = mapped_column(
        Enum(TestType, name="test_type", schema="exam"),
        nullable=False,
        default=TestType.PRACTICE,
    )

    # ── Configuration ────────────────────────────────────────────────────
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    negative_marking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    question_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(Uuid), nullable=False, default=[])

    # ── Schedule ─────────────────────────────────────────────────────────
    schedule_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    schedule_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Publishing ───────────────────────────────────────────────────────
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    r2_questions_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ── Settings (JSONB for flexible config) ─────────────────────────────
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Ownership ────────────────────────────────────────────────────────
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
