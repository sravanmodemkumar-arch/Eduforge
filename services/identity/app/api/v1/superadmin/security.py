"""Super Admin Security Center API — audit logs, sessions, IP blocks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.session import Session
from app.models.superadmin import AuditLog, IPBlock
from app.models.user import User
from shared.auth.dependencies import UserToken
from shared.schemas.common import PaginatedResponse, ResponseSchema

from .dependencies import require_admin, require_super_admin

router = APIRouter(prefix="/security", tags=["SA › Security"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class AuditLogItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    user_name: str | None = None
    user_role: str | None = None
    ip_address: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    description: str | None = None
    details: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str | None = None
    user_role: str | None = None
    ip_address: str | None = None
    device_info: dict | None = None
    created_at: datetime
    expires_at: datetime
    is_revoked: bool = False

    model_config = {"from_attributes": True}


class IPBlockItem(BaseModel):
    id: uuid.UUID
    ip_address: str
    ip_range: str | None = None
    reason: str | None = None
    blocked_by: str | None = None
    is_auto: bool = False
    is_active: bool = True
    expires_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IPBlockCreate(BaseModel):
    ip_address: str = Field(..., min_length=1, max_length=45)
    ip_range: str | None = None
    reason: str | None = None
    expires_at: datetime | None = None


# ---------------------------------------------------------------------------
# Audit Log Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/audit-log",
    response_model=ResponseSchema[PaginatedResponse[AuditLogItem]],
    summary="Paginated audit log",
)
async def list_audit_log(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[AuditLogItem]]:
    """List audit log entries with filters and pagination."""

    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)

    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)

    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
        count_query = count_query.where(AuditLog.created_at >= start_date)

    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
        count_query = count_query.where(AuditLog.created_at <= end_date)

    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        query.order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    entries = result.scalars().all()

    items = [
        AuditLogItem(
            id=e.id,
            user_id=e.user_id,
            user_name=e.user_name,
            user_role=e.user_role,
            ip_address=e.ip_address,
            action=e.action,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            description=e.description,
            details=e.details,
            created_at=e.created_at,
        )
        for e in entries
    ]

    paginated = PaginatedResponse[AuditLogItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


# ---------------------------------------------------------------------------
# Session Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/sessions",
    response_model=ResponseSchema[PaginatedResponse[SessionItem]],
    summary="List active sessions",
)
async def list_active_sessions(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[SessionItem]]:
    """List active (non-revoked, non-expired) sessions."""

    now = datetime.now(timezone.utc)

    base_filters = [
        Session.is_revoked.is_(False),
        Session.expires_at > now,
    ]
    if user_id:
        base_filters.append(Session.user_id == user_id)

    count_query = select(func.count()).select_from(Session).where(*base_filters)
    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        select(Session)
        .where(*base_filters)
        .order_by(Session.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    # Fetch user info for display
    items: list[SessionItem] = []
    for sess in sessions:
        user_result = await db.execute(
            select(User.full_name, User.primary_role).where(User.id == sess.user_id)
        )
        user_row = user_result.one_or_none()

        items.append(
            SessionItem(
                id=sess.id,
                user_id=sess.user_id,
                user_name=user_row.full_name if user_row else None,
                user_role=user_row.primary_role if user_row else None,
                ip_address=sess.ip_address,
                device_info=sess.device_info,
                created_at=sess.created_at,
                expires_at=sess.expires_at,
                is_revoked=sess.is_revoked,
            )
        )

    paginated = PaginatedResponse[SessionItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


@router.post(
    "/sessions/{session_id}/terminate",
    response_model=ResponseSchema[None],
    summary="Terminate a session",
)
async def terminate_session(
    session_id: uuid.UUID,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[None]:
    """Terminate (revoke) a specific session."""

    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already revoked",
        )

    session.is_revoked = True
    await db.flush()

    return ResponseSchema(message="Session terminated successfully")


# ---------------------------------------------------------------------------
# IP Block Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/ip-blocks",
    response_model=ResponseSchema[list[IPBlockItem]],
    summary="List blocked IPs",
)
async def list_ip_blocks(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True),
) -> ResponseSchema[list[IPBlockItem]]:
    """List blocked IP addresses."""

    query = select(IPBlock).order_by(IPBlock.created_at.desc())
    if active_only:
        query = query.where(IPBlock.is_active.is_(True))

    result = await db.execute(query)
    blocks = result.scalars().all()

    items = [
        IPBlockItem(
            id=b.id,
            ip_address=b.ip_address,
            ip_range=b.ip_range,
            reason=b.reason,
            blocked_by=b.blocked_by,
            is_auto=b.is_auto,
            is_active=b.is_active,
            expires_at=b.expires_at,
            created_at=b.created_at,
        )
        for b in blocks
    ]
    return ResponseSchema(data=items)


@router.post(
    "/ip-blocks",
    response_model=ResponseSchema[IPBlockItem],
    status_code=status.HTTP_201_CREATED,
    summary="Block an IP address",
)
async def create_ip_block(
    body: IPBlockCreate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[IPBlockItem]:
    """Block an IP address or range."""

    # Check if already blocked
    existing = await db.execute(
        select(IPBlock).where(
            IPBlock.ip_address == body.ip_address,
            IPBlock.is_active.is_(True),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"IP '{body.ip_address}' is already blocked",
        )

    block = IPBlock(
        ip_address=body.ip_address,
        ip_range=body.ip_range,
        reason=body.reason,
        blocked_by=str(current_user.user_id),
        is_auto=False,
        is_active=True,
        expires_at=body.expires_at,
    )
    db.add(block)
    await db.flush()
    await db.refresh(block)

    item = IPBlockItem(
        id=block.id,
        ip_address=block.ip_address,
        ip_range=block.ip_range,
        reason=block.reason,
        blocked_by=block.blocked_by,
        is_auto=block.is_auto,
        is_active=block.is_active,
        expires_at=block.expires_at,
        created_at=block.created_at,
    )
    return ResponseSchema(data=item, message="IP blocked successfully")


@router.delete(
    "/ip-blocks/{block_id}",
    response_model=ResponseSchema[None],
    summary="Unblock an IP address",
)
async def delete_ip_block(
    block_id: uuid.UUID,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[None]:
    """Unblock an IP address (deactivate the block rule)."""

    result = await db.execute(select(IPBlock).where(IPBlock.id == block_id))
    block = result.scalar_one_or_none()
    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP block rule not found",
        )

    block.is_active = False
    await db.flush()

    return ResponseSchema(message="IP unblocked successfully")
