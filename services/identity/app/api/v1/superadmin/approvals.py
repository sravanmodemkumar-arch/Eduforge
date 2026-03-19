"""Super Admin Approval Workflow API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.superadmin import ApprovalRequest
from shared.auth.dependencies import UserToken
from shared.schemas.common import PaginatedResponse, ResponseSchema

from .dependencies import require_admin, require_super_admin

router = APIRouter(prefix="/approvals", tags=["SA › Approvals"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ApprovalItem(BaseModel):
    id: uuid.UUID
    request_type: str
    title: str
    description: str | None = None
    details: dict | None = None
    priority: str = "MEDIUM"
    status: str = "PENDING"
    requested_by: uuid.UUID
    requested_by_name: str | None = None
    approved_by: uuid.UUID | None = None
    comment: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalActionRequest(BaseModel):
    comment: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ResponseSchema[PaginatedResponse[ApprovalItem]],
    summary="List approval requests",
)
async def list_approvals(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    request_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[ApprovalItem]]:
    """List approval requests with optional status filter."""

    query = select(ApprovalRequest)
    count_query = select(func.count()).select_from(ApprovalRequest)

    if status_filter:
        query = query.where(ApprovalRequest.status == status_filter)
        count_query = count_query.where(ApprovalRequest.status == status_filter)

    if priority:
        query = query.where(ApprovalRequest.priority == priority)
        count_query = count_query.where(ApprovalRequest.priority == priority)

    if request_type:
        query = query.where(ApprovalRequest.request_type == request_type)
        count_query = count_query.where(ApprovalRequest.request_type == request_type)

    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        query.order_by(ApprovalRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    approvals = result.scalars().all()

    items = [
        ApprovalItem(
            id=a.id,
            request_type=a.request_type,
            title=a.title,
            description=a.description,
            details=a.details,
            priority=a.priority,
            status=a.status,
            requested_by=a.requested_by,
            requested_by_name=a.requested_by_name,
            approved_by=a.approved_by,
            comment=a.comment,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in approvals
    ]

    paginated = PaginatedResponse[ApprovalItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


@router.post(
    "/{approval_id}/approve",
    response_model=ResponseSchema[ApprovalItem],
    summary="Approve request",
)
async def approve_request(
    approval_id: uuid.UUID,
    body: ApprovalActionRequest | None = None,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[ApprovalItem]:
    """Approve a pending approval request."""

    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    if approval.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve a request with status '{approval.status}'",
        )

    approval.status = "APPROVED"
    approval.approved_by = current_user.user_id
    if body and body.comment:
        approval.comment = body.comment

    await db.flush()
    await db.refresh(approval)

    item = ApprovalItem(
        id=approval.id,
        request_type=approval.request_type,
        title=approval.title,
        description=approval.description,
        details=approval.details,
        priority=approval.priority,
        status=approval.status,
        requested_by=approval.requested_by,
        requested_by_name=approval.requested_by_name,
        approved_by=approval.approved_by,
        comment=approval.comment,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
    )
    return ResponseSchema(data=item, message="Request approved successfully")


@router.post(
    "/{approval_id}/reject",
    response_model=ResponseSchema[ApprovalItem],
    summary="Reject request",
)
async def reject_request(
    approval_id: uuid.UUID,
    body: ApprovalActionRequest | None = None,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[ApprovalItem]:
    """Reject a pending approval request."""

    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )

    if approval.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject a request with status '{approval.status}'",
        )

    approval.status = "REJECTED"
    approval.approved_by = current_user.user_id
    if body and body.comment:
        approval.comment = body.comment

    await db.flush()
    await db.refresh(approval)

    item = ApprovalItem(
        id=approval.id,
        request_type=approval.request_type,
        title=approval.title,
        description=approval.description,
        details=approval.details,
        priority=approval.priority,
        status=approval.status,
        requested_by=approval.requested_by,
        requested_by_name=approval.requested_by_name,
        approved_by=approval.approved_by,
        comment=approval.comment,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
    )
    return ResponseSchema(data=item, message="Request rejected")
