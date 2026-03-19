"""Subscription SQLAlchemy model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.payment import Base


class PlanType(str, enum.Enum):
    """Subscription plan type."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ANNUAL = "annual"


class Subscription(Base):
    """Represents an institution subscription plan."""

    __tablename__ = "subscriptions"
    __table_args__ = {"schema": "billing"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    plan_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    plan_type: Mapped[PlanType] = mapped_column(
        Enum(PlanType, name="plan_type", schema="billing"),
        nullable=False,
    )
    amount_per_student: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    max_students: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    auto_renew: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.id} plan={self.plan_name}>"
