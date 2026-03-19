"""Razorpay payment integration service."""

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from typing import Any

import razorpay
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    PaymentError,
    PaymentNotFoundError,
    SignatureVerificationError,
    WebhookError,
)
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import CreateOrderRequest

logger = logging.getLogger(__name__)

_razorpay_client: razorpay.Client | None = None


def _get_razorpay_client() -> razorpay.Client:
    """Return a lazily-initialised Razorpay client."""
    global _razorpay_client  # noqa: PLW0603
    if _razorpay_client is None:
        _razorpay_client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
        )
    return _razorpay_client


async def create_order(
    session: AsyncSession,
    request: CreateOrderRequest,
) -> dict[str, Any]:
    """Create a Razorpay order and persist a payment record.

    Returns a dict with ``payment_id``, ``razorpay_order_id``, ``amount``,
    ``currency``, and ``razorpay_key_id``.
    """
    client = _get_razorpay_client()

    # Amount in paise (smallest currency unit for INR)
    amount_paise = int(request.amount * 100)

    try:
        order = client.order.create(
            data={
                "amount": amount_paise,
                "currency": request.currency,
                "notes": {
                    "institution_id": str(request.institution_id),
                    "user_id": str(request.user_id),
                },
            }
        )
    except Exception as exc:
        logger.error("Razorpay order creation failed: %s", exc)
        raise PaymentError(detail=f"Failed to create Razorpay order: {exc}") from exc

    payment = Payment(
        institution_id=request.institution_id,
        user_id=request.user_id,
        amount=request.amount,
        currency=request.currency,
        razorpay_order_id=order["id"],
        status=PaymentStatus.CREATED,
        description=request.description,
        metadata_=request.metadata or {},
    )

    session.add(payment)
    await session.commit()
    await session.refresh(payment)

    return {
        "payment_id": payment.id,
        "razorpay_order_id": order["id"],
        "amount": request.amount,
        "currency": request.currency,
        "razorpay_key_id": settings.razorpay_key_id,
    }


async def verify_payment(
    session: AsyncSession,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> Payment:
    """Verify a Razorpay payment signature and update the payment record.

    Raises ``SignatureVerificationError`` if the HMAC check fails.
    """
    # HMAC-SHA256 signature verification
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(
        key=settings.razorpay_key_secret.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, razorpay_signature):
        logger.warning(
            "Signature mismatch for order %s",
            razorpay_order_id,
        )
        raise SignatureVerificationError()

    stmt = select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()

    if payment is None:
        raise PaymentNotFoundError(razorpay_order_id)

    payment.razorpay_payment_id = razorpay_payment_id
    payment.status = PaymentStatus.CAPTURED

    # Fetch payment details from Razorpay for the method used
    try:
        client = _get_razorpay_client()
        rp_payment = client.payment.fetch(razorpay_payment_id)
        payment.method = rp_payment.get("method")
    except Exception:
        logger.warning("Could not fetch payment details from Razorpay")

    await session.commit()
    await session.refresh(payment)
    return payment


async def process_webhook(
    session: AsyncSession,
    event: str,
    payload: dict[str, Any],
    raw_body: bytes,
    signature: str,
) -> None:
    """Process an incoming Razorpay webhook event.

    Verifies the webhook signature, then updates the corresponding payment
    record based on the event type.
    """
    # Verify webhook signature
    expected = hmac.new(
        key=settings.razorpay_webhook_secret.encode(),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise WebhookError(detail="Invalid webhook signature")

    payment_entity = (
        payload.get("payment", {}).get("entity", {})
        if "payment" in payload
        else {}
    )
    order_id = payment_entity.get("order_id")

    if not order_id:
        logger.info("Webhook event %s has no order_id, skipping", event)
        return

    stmt = select(Payment).where(Payment.razorpay_order_id == order_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()

    if payment is None:
        logger.warning("No payment found for order %s from webhook", order_id)
        return

    status_map: dict[str, PaymentStatus] = {
        "payment.authorized": PaymentStatus.AUTHORIZED,
        "payment.captured": PaymentStatus.CAPTURED,
        "payment.failed": PaymentStatus.FAILED,
    }

    new_status = status_map.get(event)
    if new_status:
        payment.status = new_status
        payment.razorpay_payment_id = payment_entity.get("id", payment.razorpay_payment_id)
        payment.method = payment_entity.get("method", payment.method)
        await session.commit()
        logger.info("Payment %s updated to %s via webhook", payment.id, new_status)
    else:
        logger.info("Unhandled webhook event: %s", event)


async def get_payment_by_id(
    session: AsyncSession,
    payment_id: uuid.UUID,
) -> Payment:
    """Fetch a single payment by primary key."""
    stmt = select(Payment).where(Payment.id == payment_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()
    if payment is None:
        raise PaymentNotFoundError(str(payment_id))
    return payment


async def list_payments(
    session: AsyncSession,
    institution_id: uuid.UUID | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Payment], int]:
    """Return a paginated list of payments, optionally filtered by institution."""
    base = select(Payment).order_by(Payment.created_at.desc())
    count_stmt = select(func.count()).select_from(Payment)

    if institution_id is not None:
        base = base.where(Payment.institution_id == institution_id)
        count_stmt = count_stmt.where(Payment.institution_id == institution_id)

    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (page - 1) * size
    stmt = base.offset(offset).limit(size)
    result = await session.execute(stmt)
    items = list(result.scalars().all())

    return items, total
