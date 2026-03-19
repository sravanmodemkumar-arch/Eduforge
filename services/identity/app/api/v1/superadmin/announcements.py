"""Super Admin Announcements API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.superadmin import Announcement
from shared.auth.dependencies import UserToken
from shared.schemas.common import PaginatedResponse, ResponseSchema

from .dependencies import require_admin, require_super_admin

router = APIRouter(prefix="/announcements", tags=["SA › Announcements"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class AnnouncementItem(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    announcement_type: str = "INFO"
    position: str = "TOP_BANNER"
    target_audience: dict[str, Any] | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    is_dismissable: bool = True
    show_once: bool = False
    requires_ack: bool = False
    is_active: bool = True
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    announcement_type: str = "INFO"
    position: str = "TOP_BANNER"
    target_audience: dict[str, Any] | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    is_dismissable: bool = True
    show_once: bool = False
    requires_ack: bool = False
    is_active: bool = True


class AnnouncementUpdate(BaseModel):
    title: str | None = None
    message: str | None = None
    announcement_type: str | None = None
    position: str | None = None
    target_audience: dict[str, Any] | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    is_dismissable: bool | None = None
    show_once: bool | None = None
    requires_ack: bool | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ResponseSchema[PaginatedResponse[AnnouncementItem]],
    summary="List announcements",
)
async def list_announcements(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(False),
    announcement_type: str | None = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[AnnouncementItem]]:
    """List announcements with optional filters."""

    query = select(Announcement)
    count_query = select(func.count()).select_from(Announcement)

    if active_only:
        query = query.where(Announcement.is_active.is_(True))
        count_query = count_query.where(Announcement.is_active.is_(True))

    if announcement_type:
        query = query.where(Announcement.announcement_type == announcement_type)
        count_query = count_query.where(Announcement.announcement_type == announcement_type)

    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        query.order_by(Announcement.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    announcements = result.scalars().all()

    items = [
        AnnouncementItem(
            id=a.id,
            title=a.title,
            message=a.message,
            announcement_type=a.announcement_type,
            position=a.position,
            target_audience=a.target_audience,
            start_at=a.start_at,
            end_at=a.end_at,
            is_dismissable=a.is_dismissable,
            show_once=a.show_once,
            requires_ack=a.requires_ack,
            is_active=a.is_active,
            created_by=a.created_by,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in announcements
    ]

    paginated = PaginatedResponse[AnnouncementItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


@router.post(
    "",
    response_model=ResponseSchema[AnnouncementItem],
    status_code=status.HTTP_201_CREATED,
    summary="Create announcement",
)
async def create_announcement(
    body: AnnouncementCreate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[AnnouncementItem]:
    """Create a new announcement."""

    announcement = Announcement(
        title=body.title,
        message=body.message,
        announcement_type=body.announcement_type,
        position=body.position,
        target_audience=body.target_audience or {},
        start_at=body.start_at,
        end_at=body.end_at,
        is_dismissable=body.is_dismissable,
        show_once=body.show_once,
        requires_ack=body.requires_ack,
        is_active=body.is_active,
        created_by=current_user.user_id,
    )
    db.add(announcement)
    await db.flush()
    await db.refresh(announcement)

    item = AnnouncementItem(
        id=announcement.id,
        title=announcement.title,
        message=announcement.message,
        announcement_type=announcement.announcement_type,
        position=announcement.position,
        target_audience=announcement.target_audience,
        start_at=announcement.start_at,
        end_at=announcement.end_at,
        is_dismissable=announcement.is_dismissable,
        show_once=announcement.show_once,
        requires_ack=announcement.requires_ack,
        is_active=announcement.is_active,
        created_by=announcement.created_by,
        created_at=announcement.created_at,
        updated_at=announcement.updated_at,
    )
    return ResponseSchema(data=item, message="Announcement created successfully")


@router.put(
    "/{announcement_id}",
    response_model=ResponseSchema[AnnouncementItem],
    summary="Update announcement",
)
async def update_announcement(
    announcement_id: uuid.UUID,
    body: AnnouncementUpdate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[AnnouncementItem]:
    """Update an existing announcement."""

    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(announcement, field_name, value)

    await db.flush()
    await db.refresh(announcement)

    item = AnnouncementItem(
        id=announcement.id,
        title=announcement.title,
        message=announcement.message,
        announcement_type=announcement.announcement_type,
        position=announcement.position,
        target_audience=announcement.target_audience,
        start_at=announcement.start_at,
        end_at=announcement.end_at,
        is_dismissable=announcement.is_dismissable,
        show_once=announcement.show_once,
        requires_ack=announcement.requires_ack,
        is_active=announcement.is_active,
        created_by=announcement.created_by,
        created_at=announcement.created_at,
        updated_at=announcement.updated_at,
    )
    return ResponseSchema(data=item, message="Announcement updated successfully")


@router.delete(
    "/{announcement_id}",
    response_model=ResponseSchema[None],
    summary="Delete announcement",
)
async def delete_announcement(
    announcement_id: uuid.UUID,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[None]:
    """Delete an announcement."""

    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )

    await db.delete(announcement)
    await db.flush()

    return ResponseSchema(message="Announcement deleted successfully")
