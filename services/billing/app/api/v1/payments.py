"""Payment API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.payment import (
    CreateOrderRequest,
    CreateOrderResponse,
    PaymentListResponse,
    PaymentResponse,
    VerifyPaymentRequest,
)
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/create-order",
    response_model=CreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Razorpay order",
)
async def create_order(
    body: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
) -> CreateOrderResponse:
    """Create a new Razorpay order and persist a payment record."""
    result = await payment_service.create_order(db, body)
    return CreateOrderResponse(**result)


@router.post(
    "/verify",
    response_model=PaymentResponse,
    summary="Verify a Razorpay payment",
)
async def verify_payment(
    body: VerifyPaymentRequest,
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    """Verify the Razorpay payment signature and mark the payment as captured."""
    payment = await payment_service.verify_payment(
        db,
        razorpay_order_id=body.razorpay_order_id,
        razorpay_payment_id=body.razorpay_payment_id,
        razorpay_signature=body.razorpay_signature,
    )
    return PaymentResponse.model_validate(payment)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Handle Razorpay webhook",
)
async def webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_razorpay_signature: str = Header(...),
) -> dict[str, str]:
    """Process an incoming Razorpay webhook event."""
    raw_body = await request.body()
    payload = await request.json()

    await payment_service.process_webhook(
        db,
        event=payload.get("event", ""),
        payload=payload.get("payload", {}),
        raw_body=raw_body,
        signature=x_razorpay_signature,
    )
    return {"status": "ok"}


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Get payment by ID",
)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    """Retrieve a single payment record by its ID."""
    payment = await payment_service.get_payment_by_id(db, payment_id)
    return PaymentResponse.model_validate(payment)


@router.get(
    "",
    response_model=PaymentListResponse,
    summary="List payments",
)
async def list_payments(
    institution_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaymentListResponse:
    """Return a paginated list of payments."""
    items, total = await payment_service.list_payments(
        db,
        institution_id=institution_id,
        page=page,
        size=size,
    )
    return PaymentListResponse(
        items=[PaymentResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        size=size,
    )
