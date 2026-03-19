"""Super Admin Subscription & Revenue Management API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.institution import Institution, SubscriptionPlan, SubscriptionStatus
from app.models.superadmin import PlanDefinition
from shared.auth.dependencies import UserToken
from shared.schemas.common import PaginatedResponse, ResponseSchema

from .dependencies import require_admin, require_super_admin

router = APIRouter(prefix="/subscriptions", tags=["SA › Subscriptions"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PlanDefinitionItem(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: str | None = None
    price_monthly: float = 0.0
    price_quarterly: float = 0.0
    price_annual: float = 0.0
    max_students: int = 100
    max_teachers: int = 10
    max_storage_gb: int = 1
    api_rate_limit: int = 100
    features: dict[str, Any] | None = None
    is_visible: bool = True
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    price_monthly: float = 0.0
    price_quarterly: float = 0.0
    price_annual: float = 0.0
    max_students: int = 100
    max_teachers: int = 10
    max_storage_gb: int = 1
    api_rate_limit: int = 100
    features: dict[str, Any] | None = None
    is_visible: bool = True
    is_active: bool = True
    sort_order: int = 0


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price_monthly: float | None = None
    price_quarterly: float | None = None
    price_annual: float | None = None
    max_students: int | None = None
    max_teachers: int | None = None
    max_storage_gb: int | None = None
    api_rate_limit: int | None = None
    features: dict[str, Any] | None = None
    is_visible: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class InstitutionSubscriptionItem(BaseModel):
    institution_id: uuid.UUID
    institution_name: str
    institution_code: str
    subscription_plan: str | None = None
    subscription_status: str | None = None
    subscription_start: datetime | None = None
    subscription_expiry: datetime | None = None
    subscription_amount: float | None = None
    auto_renew: bool = True
    billing_cycle: str | None = None

    model_config = {"from_attributes": True}


class RevenueSummary(BaseModel):
    total_mrr: float = 0.0
    total_arr: float = 0.0
    active_subscriptions: int = 0
    trial_subscriptions: int = 0
    expired_subscriptions: int = 0
    revenue_by_plan: list[RevenuePlanBreakdown] = Field(default_factory=list)


class RevenuePlanBreakdown(BaseModel):
    plan: str
    count: int = 0
    total_amount: float = 0.0


class RevenueForecast(BaseModel):
    current_mrr: float = 0.0
    projected_next_month: float = 0.0
    projected_next_quarter: float = 0.0
    expiring_this_month: int = 0
    expiring_next_month: int = 0
    churn_risk_count: int = 0


# ---------------------------------------------------------------------------
# Plan Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/plans",
    response_model=ResponseSchema[list[PlanDefinitionItem]],
    summary="List plan definitions",
)
async def list_plans(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[list[PlanDefinitionItem]]:
    """List all subscription plan definitions."""

    result = await db.execute(
        select(PlanDefinition).order_by(PlanDefinition.sort_order, PlanDefinition.created_at)
    )
    plans = result.scalars().all()

    items = [
        PlanDefinitionItem(
            id=p.id,
            name=p.name,
            code=p.code,
            description=p.description,
            price_monthly=p.price_monthly,
            price_quarterly=p.price_quarterly,
            price_annual=p.price_annual,
            max_students=p.max_students,
            max_teachers=p.max_teachers,
            max_storage_gb=p.max_storage_gb,
            api_rate_limit=p.api_rate_limit,
            features=p.features,
            is_visible=p.is_visible,
            is_active=p.is_active,
            sort_order=p.sort_order,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in plans
    ]
    return ResponseSchema(data=items)


@router.post(
    "/plans",
    response_model=ResponseSchema[PlanDefinitionItem],
    status_code=status.HTTP_201_CREATED,
    summary="Create plan definition",
)
async def create_plan(
    body: PlanCreate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[PlanDefinitionItem]:
    """Create a new subscription plan definition."""

    # Check duplicate code
    existing = await db.execute(
        select(PlanDefinition).where(PlanDefinition.code == body.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Plan with code '{body.code}' already exists",
        )

    plan = PlanDefinition(
        name=body.name,
        code=body.code,
        description=body.description,
        price_monthly=body.price_monthly,
        price_quarterly=body.price_quarterly,
        price_annual=body.price_annual,
        max_students=body.max_students,
        max_teachers=body.max_teachers,
        max_storage_gb=body.max_storage_gb,
        api_rate_limit=body.api_rate_limit,
        features=body.features or {},
        is_visible=body.is_visible,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)

    item = PlanDefinitionItem(
        id=plan.id,
        name=plan.name,
        code=plan.code,
        description=plan.description,
        price_monthly=plan.price_monthly,
        price_quarterly=plan.price_quarterly,
        price_annual=plan.price_annual,
        max_students=plan.max_students,
        max_teachers=plan.max_teachers,
        max_storage_gb=plan.max_storage_gb,
        api_rate_limit=plan.api_rate_limit,
        features=plan.features,
        is_visible=plan.is_visible,
        is_active=plan.is_active,
        sort_order=plan.sort_order,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )
    return ResponseSchema(data=item, message="Plan created successfully")


@router.put(
    "/plans/{plan_id}",
    response_model=ResponseSchema[PlanDefinitionItem],
    summary="Update plan definition",
)
async def update_plan(
    plan_id: uuid.UUID,
    body: PlanUpdate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[PlanDefinitionItem]:
    """Update an existing plan definition."""

    result = await db.execute(
        select(PlanDefinition).where(PlanDefinition.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(plan, field_name, value)

    await db.flush()
    await db.refresh(plan)

    item = PlanDefinitionItem(
        id=plan.id,
        name=plan.name,
        code=plan.code,
        description=plan.description,
        price_monthly=plan.price_monthly,
        price_quarterly=plan.price_quarterly,
        price_annual=plan.price_annual,
        max_students=plan.max_students,
        max_teachers=plan.max_teachers,
        max_storage_gb=plan.max_storage_gb,
        api_rate_limit=plan.api_rate_limit,
        features=plan.features,
        is_visible=plan.is_visible,
        is_active=plan.is_active,
        sort_order=plan.sort_order,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )
    return ResponseSchema(data=item, message="Plan updated successfully")


# ---------------------------------------------------------------------------
# Subscription Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ResponseSchema[PaginatedResponse[InstitutionSubscriptionItem]],
    summary="List all institution subscriptions",
)
async def list_subscriptions(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    plan: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[InstitutionSubscriptionItem]]:
    """List all institution subscriptions with optional filters."""

    query = select(Institution).where(Institution.deleted_at.is_(None))
    count_query = (
        select(func.count())
        .select_from(Institution)
        .where(Institution.deleted_at.is_(None))
    )

    if plan:
        query = query.where(Institution.subscription_plan == plan)
        count_query = count_query.where(Institution.subscription_plan == plan)

    if status_filter:
        query = query.where(Institution.subscription_status == status_filter)
        count_query = count_query.where(Institution.subscription_status == status_filter)

    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = query.order_by(Institution.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    institutions = result.scalars().all()

    items = [
        InstitutionSubscriptionItem(
            institution_id=inst.id,
            institution_name=inst.name,
            institution_code=inst.code,
            subscription_plan=(
                inst.subscription_plan.value if inst.subscription_plan else None
            ),
            subscription_status=(
                inst.subscription_status.value if inst.subscription_status else None
            ),
            subscription_start=inst.subscription_start,
            subscription_expiry=inst.subscription_expiry,
            subscription_amount=inst.subscription_amount,
            auto_renew=inst.auto_renew,
            billing_cycle=inst.billing_cycle,
        )
        for inst in institutions
    ]

    paginated = PaginatedResponse[InstitutionSubscriptionItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


# ---------------------------------------------------------------------------
# Revenue Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/revenue",
    response_model=ResponseSchema[RevenueSummary],
    summary="Revenue dashboard data",
)
async def get_revenue_dashboard(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[RevenueSummary]:
    """Return revenue dashboard data with plan-level breakdown."""

    # Active subscriptions revenue (MRR)
    mrr_result = await db.execute(
        select(func.coalesce(func.sum(Institution.subscription_amount), 0.0))
        .select_from(Institution)
        .where(
            Institution.subscription_status.in_(["ACTIVE"]),
            Institution.deleted_at.is_(None),
        )
    )
    total_mrr = float(mrr_result.scalar_one())
    total_arr = total_mrr * 12

    # Subscription status counts
    active_result = await db.execute(
        select(func.count())
        .select_from(Institution)
        .where(
            Institution.subscription_status == "ACTIVE",
            Institution.deleted_at.is_(None),
        )
    )
    active_subscriptions = active_result.scalar_one()

    trial_result = await db.execute(
        select(func.count())
        .select_from(Institution)
        .where(
            Institution.subscription_status == "TRIAL",
            Institution.deleted_at.is_(None),
        )
    )
    trial_subscriptions = trial_result.scalar_one()

    expired_result = await db.execute(
        select(func.count())
        .select_from(Institution)
        .where(
            Institution.subscription_status == "EXPIRED",
            Institution.deleted_at.is_(None),
        )
    )
    expired_subscriptions = expired_result.scalar_one()

    # Revenue by plan
    plan_breakdown_result = await db.execute(
        select(
            Institution.subscription_plan,
            func.count().label("count"),
            func.coalesce(func.sum(Institution.subscription_amount), 0.0).label("total"),
        )
        .where(
            Institution.subscription_plan.isnot(None),
            Institution.deleted_at.is_(None),
        )
        .group_by(Institution.subscription_plan)
    )
    plan_rows = plan_breakdown_result.all()

    revenue_by_plan = [
        RevenuePlanBreakdown(
            plan=row.subscription_plan.value if hasattr(row.subscription_plan, "value") else str(row.subscription_plan),
            count=row.count,
            total_amount=float(row.total),
        )
        for row in plan_rows
    ]

    summary = RevenueSummary(
        total_mrr=total_mrr,
        total_arr=total_arr,
        active_subscriptions=active_subscriptions,
        trial_subscriptions=trial_subscriptions,
        expired_subscriptions=expired_subscriptions,
        revenue_by_plan=revenue_by_plan,
    )
    return ResponseSchema(data=summary)


@router.get(
    "/revenue/forecast",
    response_model=ResponseSchema[RevenueForecast],
    summary="Revenue forecast",
)
async def get_revenue_forecast(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[RevenueForecast]:
    """Return revenue forecast based on current subscriptions and expiry dates."""

    now = datetime.now(timezone.utc)

    # Current MRR
    mrr_result = await db.execute(
        select(func.coalesce(func.sum(Institution.subscription_amount), 0.0))
        .select_from(Institution)
        .where(
            Institution.subscription_status == "ACTIVE",
            Institution.deleted_at.is_(None),
        )
    )
    current_mrr = float(mrr_result.scalar_one())

    # Expiring this month
    from datetime import timedelta

    end_of_month = now.replace(day=28) + timedelta(days=4)
    end_of_month = end_of_month.replace(day=1) - timedelta(days=1)

    expiring_this_month_result = await db.execute(
        select(func.count())
        .select_from(Institution)
        .where(
            Institution.subscription_expiry.isnot(None),
            Institution.subscription_expiry <= end_of_month,
            Institution.subscription_expiry >= now,
            Institution.deleted_at.is_(None),
        )
    )
    expiring_this_month = expiring_this_month_result.scalar_one()

    # Expiring next month
    start_next_month = end_of_month + timedelta(days=1)
    end_next_month = (start_next_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    expiring_next_month_result = await db.execute(
        select(func.count())
        .select_from(Institution)
        .where(
            Institution.subscription_expiry.isnot(None),
            Institution.subscription_expiry >= start_next_month,
            Institution.subscription_expiry <= end_next_month,
            Institution.deleted_at.is_(None),
        )
    )
    expiring_next_month = expiring_next_month_result.scalar_one()

    # Churn risk: expired or expiring soon without auto_renew
    churn_risk_result = await db.execute(
        select(func.count())
        .select_from(Institution)
        .where(
            Institution.subscription_expiry.isnot(None),
            Institution.subscription_expiry <= end_of_month,
            Institution.auto_renew.is_(False),
            Institution.deleted_at.is_(None),
        )
    )
    churn_risk_count = churn_risk_result.scalar_one()

    forecast = RevenueForecast(
        current_mrr=current_mrr,
        projected_next_month=current_mrr,  # Simplified: assumes stable MRR
        projected_next_quarter=current_mrr * 3,
        expiring_this_month=expiring_this_month,
        expiring_next_month=expiring_next_month,
        churn_risk_count=churn_risk_count,
    )
    return ResponseSchema(data=forecast)
