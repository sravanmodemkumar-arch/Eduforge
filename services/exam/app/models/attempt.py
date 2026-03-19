from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SubmitSource(str, enum.Enum):
    MANUAL = "MANUAL"
    AUTO_TIMER = "AUTO_TIMER"
    FORCE_SUBMIT = "FORCE_SUBMIT"


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = {"schema": "exam"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("exam.exam_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exam.tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    institution_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)

    # ── Answer data ──────────────────────────────────────────────────────
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False)
    time_taken_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    submit_source: Mapped[SubmitSource] = mapped_column(
        Enum(SubmitSource, name="submit_source", schema="exam"),
        nullable=False,
        default=SubmitSource.MANUAL,
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
