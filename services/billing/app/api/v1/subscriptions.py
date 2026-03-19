"""Subscription API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SubscriptionNotFoundError
from app.core.database import get_db
from app.models.subscription import Subscription
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionListResponse,
    SubscriptionResponse,
    SubscriptionUpdate,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a subscription",
)
async def create_subscription(
    body: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Create a new subscription for an institution."""
    subscription = Subscription(
        institution_id=body.institution_id,
        plan_name=body.plan_name,
        plan_type=body.plan_type,
        amount_per_student=body.amount_per_student,
        max_students=body.max_students,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return SubscriptionResponse.model_validate(subscription)


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Get subscription by ID",
)
async def get_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Retrieve a single subscription by its ID."""
    stmt = select(Subscription).where(Subscription.id == subscription_id)
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise SubscriptionNotFoundError(str(subscription_id))
    return SubscriptionResponse.model_validate(subscription)


@router.get(
    "",
    response_model=SubscriptionListResponse,
    summary="List subscriptions",
)
async def list_subscriptions(
    institution_id: uuid.UUID | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionListResponse:
    """Return a paginated list of subscriptions."""
    base = select(Subscription).order_by(Subscription.created_at.desc())
    count_stmt = select(func.count()).select_from(Subscription)

    if institution_id is not None:
        base = base.where(Subscription.institution_id == institution_id)
        count_stmt = count_stmt.where(Subscription.institution_id == institution_id)

    if is_active is not None:
        base = base.where(Subscription.is_active == is_active)
        count_stmt = count_stmt.where(Subscription.is_active == is_active)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (page - 1) * size
    stmt = base.offset(offset).limit(size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return SubscriptionListResponse(
        items=[SubscriptionResponse.model_validate(s) for s in items],
        total=total,
        page=page,
        size=size,
    )


@router.patch(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    summary="Update a subscription",
)
async def update_subscription(
    subscription_id: uuid.UUID,
    body: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Partially update an existing subscription."""
    stmt = select(Subscription).where(Subscription.id == subscription_id)
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise SubscriptionNotFoundError(str(subscription_id))

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)

    await db.commit()
    await db.refresh(subscription)
    return SubscriptionResponse.model_validate(subscription)


@router.delete(
    "/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a subscription",
)
async def deactivate_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a subscription by setting is_active to False."""
    stmt = select(Subscription).where(Subscription.id == subscription_id)
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise SubscriptionNotFoundError(str(subscription_id))

    subscription.is_active = False
    await db.commit()
