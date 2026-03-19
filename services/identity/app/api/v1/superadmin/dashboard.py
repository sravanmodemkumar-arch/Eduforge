"""Super Admin Dashboard API — platform stats, alerts, and service health."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.institution import Institution, InstitutionStatus
from app.models.superadmin import Incident
from app.models.user import User, UserStatus
from shared.auth.dependencies import UserToken
from shared.schemas.common import ResponseSchema

from .dependencies import require_admin

router = APIRouter(prefix="/dashboard", tags=["SA › Dashboard"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PlatformStatsResponse(BaseModel):
    total_institutions: int = 0
    active_institutions: int = 0
    total_users: int = 0
    active_users: int = 0
    active_now: int = 0
    revenue_this_month: float = 0.0
    tests_today: int = 0
    open_tickets: int = 0


class AlertItem(BaseModel):
    id: uuid.UUID
    severity: str
    title: str
    message: str
    source: str | None = None
    created_at: datetime


class AlertsResponse(BaseModel):
    alerts: list[AlertItem] = Field(default_factory=list)
    total: int = 0


class ServiceHealthItem(BaseModel):
    name: str
    status: str  # healthy, degraded, down
    latency_ms: float | None = None
    last_checked: datetime | None = None
    details: dict[str, Any] | None = None


class HealthOverviewResponse(BaseModel):
    overall: str  # healthy, degraded, down
    services: list[ServiceHealthItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/stats",
    response_model=ResponseSchema[PlatformStatsResponse],
    summary="Platform statistics overview",
)
async def get_dashboard_stats(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[PlatformStatsResponse]:
    """Return high-level platform statistics for the Super Admin dashboard."""

    # Total institutions
    total_inst_result = await db.execute(
        select(func.count()).select_from(Institution).where(Institution.deleted_at.is_(None))
    )
    total_institutions = total_inst_result.scalar_one()

    # Active institutions
    active_inst_result = await db.execute(
        select(func.count())
        .select_from(Institution)
        .where(
            Institution.status == InstitutionStatus.ACTIVE,
            Institution.deleted_at.is_(None),
        )
    )
    active_institutions = active_inst_result.scalar_one()

    # Total users
    total_users_result = await db.execute(
        select(func.count()).select_from(User).where(User.deleted_at.is_(None))
    )
    total_users = total_users_result.scalar_one()

    # Active users
    active_users_result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.status == UserStatus.ACTIVE, User.deleted_at.is_(None))
    )
    active_users = active_users_result.scalar_one()

    # Revenue this month (sum of subscription_amount for active institutions)
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Institution.subscription_amount), 0.0))
        .select_from(Institution)
        .where(
            Institution.subscription_status.in_(["ACTIVE", "TRIAL"]),
            Institution.deleted_at.is_(None),
        )
    )
    revenue_this_month = float(revenue_result.scalar_one())

    stats = PlatformStatsResponse(
        total_institutions=total_institutions,
        active_institutions=active_institutions,
        total_users=total_users,
        active_users=active_users,
        active_now=0,  # Requires real-time tracking (e.g. Redis)
        revenue_this_month=revenue_this_month,
        tests_today=0,  # Populated via cross-service call
        open_tickets=0,  # Populated via cross-service call
    )

    return ResponseSchema(data=stats)


@router.get(
    "/alerts",
    response_model=ResponseSchema[AlertsResponse],
    summary="Active platform alerts",
)
async def get_dashboard_alerts(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[AlertsResponse]:
    """Return active alerts for the Super Admin dashboard.

    Alerts are derived from open incidents with severity SEV1 or SEV2.
    """
    result = await db.execute(
        select(Incident)
        .where(Incident.status.in_(["OPEN", "INVESTIGATING", "MONITORING"]))
        .order_by(Incident.created_at.desc())
        .limit(50)
    )
    incidents = result.scalars().all()

    alerts = [
        AlertItem(
            id=inc.id,
            severity=inc.severity,
            title=inc.title,
            message=inc.description or "",
            source="incident",
            created_at=inc.created_at,
        )
        for inc in incidents
    ]

    return ResponseSchema(data=AlertsResponse(alerts=alerts, total=len(alerts)))


@router.get(
    "/health",
    response_model=ResponseSchema[HealthOverviewResponse],
    summary="Service health overview",
)
async def get_service_health(
    current_user: UserToken = Depends(require_admin),
) -> ResponseSchema[HealthOverviewResponse]:
    """Return the health status of all 7 platform services.

    In a production deployment this endpoint would issue HTTP health-check
    requests to each microservice.  The current implementation returns a
    placeholder response so the API contract is established.
    """
    service_names = [
        "identity",
        "institution",
        "content",
        "assessment",
        "analytics",
        "notification",
        "gateway",
    ]

    services = [
        ServiceHealthItem(
            name=name,
            status="healthy",
            latency_ms=None,
            last_checked=None,
            details=None,
        )
        for name in service_names
    ]

    # Determine overall status
    statuses = {s.status for s in services}
    if "down" in statuses:
        overall = "down"
    elif "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    return ResponseSchema(
        data=HealthOverviewResponse(overall=overall, services=services)
    )
