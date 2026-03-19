"""Pydantic schemas for payment endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment import PaymentStatus


# ── Request schemas ──────────────────────────────────────────────────────


class CreateOrderRequest(BaseModel):
    """Request body for creating a Razorpay order."""

    institution_id: uuid.UUID
    user_id: uuid.UUID
    amount: float = Field(..., gt=0, description="Amount in INR")
    currency: str = Field(default="INR", max_length=3)
    description: str | None = None
    metadata: dict[str, Any] | None = None


class VerifyPaymentRequest(BaseModel):
    """Request body for verifying a Razorpay payment."""

    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class WebhookPayload(BaseModel):
    """Razorpay webhook payload."""

    model_config = ConfigDict(extra="allow")

    event: str
    payload: dict[str, Any]


# ── Response schemas ─────────────────────────────────────────────────────


class PaymentResponse(BaseModel):
    """Standard payment response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    currency: str
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    status: PaymentStatus
    method: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = Field(None, alias="metadata_")
    created_at: datetime
    updated_at: datetime


class CreateOrderResponse(BaseModel):
    """Response after creating a Razorpay order."""

    payment_id: uuid.UUID
    razorpay_order_id: str
    amount: float
    currency: str
    razorpay_key_id: str


class PaymentListResponse(BaseModel):
    """Paginated list of payments."""

    items: list[PaymentResponse]
    total: int
    page: int
    size: int
