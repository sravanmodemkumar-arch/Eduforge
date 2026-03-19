"""Super Admin Incident Management API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.superadmin import Incident
from shared.auth.dependencies import UserToken
from shared.schemas.common import PaginatedResponse, ResponseSchema

from .dependencies import require_admin, require_super_admin

router = APIRouter(prefix="/incidents", tags=["SA › Incidents"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class IncidentItem(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    severity: str
    status: str
    affected_services: list[Any] | None = None
    affected_institutions: list[Any] | None = None
    root_cause: str | None = None
    resolution: str | None = None
    postmortem_url: str | None = None
    created_by: uuid.UUID | None = None
    resolved_by: uuid.UUID | None = None
    resolved_at: datetime | None = None
    timeline: list[Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    severity: str = Field(..., pattern="^SEV[1-4]$")
    affected_services: list[str] | None = None
    affected_institutions: list[uuid.UUID] | None = None


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = Field(None, pattern="^SEV[1-4]$")
    status: str | None = None
    affected_services: list[str] | None = None
    affected_institutions: list[uuid.UUID] | None = None
    root_cause: str | None = None
    postmortem_url: str | None = None
    timeline: list[Any] | None = None


class IncidentResolveRequest(BaseModel):
    resolution: str = Field(..., min_length=1)
    root_cause: str | None = None
    postmortem_url: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ResponseSchema[PaginatedResponse[IncidentItem]],
    summary="List incidents",
)
async def list_incidents(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    severity: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[IncidentItem]]:
    """List incidents with optional filters."""

    query = select(Incident)
    count_query = select(func.count()).select_from(Incident)

    if severity:
        query = query.where(Incident.severity == severity)
        count_query = count_query.where(Incident.severity == severity)

    if status_filter:
        query = query.where(Incident.status == status_filter)
        count_query = count_query.where(Incident.status == status_filter)

    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        query.order_by(Incident.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    incidents = result.scalars().all()

    items = [
        IncidentItem(
            id=inc.id,
            title=inc.title,
            description=inc.description,
            severity=inc.severity,
            status=inc.status,
            affected_services=inc.affected_services,
            affected_institutions=inc.affected_institutions,
            root_cause=inc.root_cause,
            resolution=inc.resolution,
            postmortem_url=inc.postmortem_url,
            created_by=inc.created_by,
            resolved_by=inc.resolved_by,
            resolved_at=inc.resolved_at,
            timeline=inc.timeline,
            created_at=inc.created_at,
            updated_at=inc.updated_at,
        )
        for inc in incidents
    ]

    paginated = PaginatedResponse[IncidentItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


@router.post(
    "",
    response_model=ResponseSchema[IncidentItem],
    status_code=status.HTTP_201_CREATED,
    summary="Create incident",
)
async def create_incident(
    body: IncidentCreate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[IncidentItem]:
    """Create a new incident."""

    now = datetime.now(timezone.utc)

    incident = Incident(
        title=body.title,
        description=body.description,
        severity=body.severity,
        status="OPEN",
        affected_services=body.affected_services or [],
        affected_institutions=[str(i) for i in (body.affected_institutions or [])],
        created_by=current_user.user_id,
        timeline=[
            {
                "timestamp": now.isoformat(),
                "action": "CREATED",
                "by": str(current_user.user_id),
                "note": f"Incident created with severity {body.severity}",
            }
        ],
    )
    db.add(incident)
    await db.flush()
    await db.refresh(incident)

    item = IncidentItem(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        affected_services=incident.affected_services,
        affected_institutions=incident.affected_institutions,
        root_cause=incident.root_cause,
        resolution=incident.resolution,
        postmortem_url=incident.postmortem_url,
        created_by=incident.created_by,
        resolved_by=incident.resolved_by,
        resolved_at=incident.resolved_at,
        timeline=incident.timeline,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )
    return ResponseSchema(data=item, message="Incident created successfully")


@router.put(
    "/{incident_id}",
    response_model=ResponseSchema[IncidentItem],
    summary="Update incident",
)
async def update_incident(
    incident_id: uuid.UUID,
    body: IncidentUpdate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[IncidentItem]:
    """Update an existing incident."""

    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    update_data = body.model_dump(exclude_unset=True)

    # Convert UUID lists to strings for JSONB storage
    if "affected_institutions" in update_data and update_data["affected_institutions"]:
        update_data["affected_institutions"] = [
            str(i) for i in update_data["affected_institutions"]
        ]

    for field_name, value in update_data.items():
        setattr(incident, field_name, value)

    # Append to timeline
    now = datetime.now(timezone.utc)
    timeline = incident.timeline or []
    timeline.append(
        {
            "timestamp": now.isoformat(),
            "action": "UPDATED",
            "by": str(current_user.user_id),
            "changes": list(update_data.keys()),
        }
    )
    incident.timeline = timeline

    await db.flush()
    await db.refresh(incident)

    item = IncidentItem(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        affected_services=incident.affected_services,
        affected_institutions=incident.affected_institutions,
        root_cause=incident.root_cause,
        resolution=incident.resolution,
        postmortem_url=incident.postmortem_url,
        created_by=incident.created_by,
        resolved_by=incident.resolved_by,
        resolved_at=incident.resolved_at,
        timeline=incident.timeline,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )
    return ResponseSchema(data=item, message="Incident updated successfully")


@router.post(
    "/{incident_id}/resolve",
    response_model=ResponseSchema[IncidentItem],
    summary="Resolve incident",
)
async def resolve_incident(
    incident_id: uuid.UUID,
    body: IncidentResolveRequest,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[IncidentItem]:
    """Resolve an incident with resolution details."""

    result = await db.execute(
        select(Incident).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    if incident.status == "RESOLVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident is already resolved",
        )

    now = datetime.now(timezone.utc)

    incident.status = "RESOLVED"
    incident.resolution = body.resolution
    incident.resolved_by = current_user.user_id
    incident.resolved_at = now

    if body.root_cause:
        incident.root_cause = body.root_cause
    if body.postmortem_url:
        incident.postmortem_url = body.postmortem_url

    # Append to timeline
    timeline = incident.timeline or []
    timeline.append(
        {
            "timestamp": now.isoformat(),
            "action": "RESOLVED",
            "by": str(current_user.user_id),
            "note": body.resolution,
        }
    )
    incident.timeline = timeline

    await db.flush()
    await db.refresh(incident)

    item = IncidentItem(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        affected_services=incident.affected_services,
        affected_institutions=incident.affected_institutions,
        root_cause=incident.root_cause,
        resolution=incident.resolution,
        postmortem_url=incident.postmortem_url,
        created_by=incident.created_by,
        resolved_by=incident.resolved_by,
        resolved_at=incident.resolved_at,
        timeline=incident.timeline,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )
    return ResponseSchema(data=item, message="Incident resolved successfully")
