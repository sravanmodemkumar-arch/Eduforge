"""Pydantic schemas for subscription endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.subscription import PlanType


# ── Request schemas ──────────────────────────────────────────────────────


class SubscriptionCreate(BaseModel):
    """Request body for creating a subscription."""

    institution_id: uuid.UUID
    plan_name: str = Field(..., min_length=1, max_length=100)
    plan_type: PlanType
    amount_per_student: float = Field(..., gt=0)
    max_students: int = Field(..., gt=0)
    starts_at: datetime
    ends_at: datetime


class SubscriptionUpdate(BaseModel):
    """Request body for updating a subscription."""

    plan_name: str | None = Field(None, min_length=1, max_length=100)
    plan_type: PlanType | None = None
    amount_per_student: float | None = Field(None, gt=0)
    max_students: int | None = Field(None, gt=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None


# ── Response schemas ─────────────────────────────────────────────────────


class SubscriptionResponse(BaseModel):
    """Standard subscription response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    plan_name: str
    plan_type: PlanType
    amount_per_student: float
    max_students: int
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SubscriptionListResponse(BaseModel):
    """Paginated list of subscriptions."""

    items: list[SubscriptionResponse]
    total: int
    page: int
    size: int
