from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"
    ABANDONED = "ABANDONED"


class ExamSession(Base):
    __tablename__ = "exam_sessions"
    __table_args__ = {"schema": "exam"}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    test_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exam.tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    institution_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)

    # ── Session details ──────────────────────────────────────────────────
    salt: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)

    # ── State ────────────────────────────────────────────────────────────
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status", schema="exam"),
        nullable=False,
        default=SessionStatus.ACTIVE,
        index=True,
    )
    answers_received: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Client metadata ──────────────────────────────────────────────────
    device_fingerprint: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
