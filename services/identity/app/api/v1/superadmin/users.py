"""Super Admin User Management API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.superadmin import ImpersonationLog
from app.models.user import User, UserRoleAssignment, UserStatus
from shared.auth.dependencies import UserToken
from shared.schemas.common import PaginatedResponse, ResponseSchema

from .dependencies import require_admin, require_super_admin

router = APIRouter(prefix="/users", tags=["SA › Users"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLATFORM_STAFF_ROLES = {
    "SUPER_ADMIN",
    "PLATFORM_ADMIN",
    "OPERATIONS_MANAGER",
    "CONTENT_MANAGER",
    "SUPPORT_AGENT",
}

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UserListItem(BaseModel):
    id: uuid.UUID
    full_name: str | None = None
    email: str | None = None
    phone: str
    primary_role: str
    institution_id: uuid.UUID | None = None
    status: str
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserDetail(BaseModel):
    id: uuid.UUID
    full_name: str | None = None
    email: str | None = None
    phone: str
    avatar_url: str | None = None
    primary_role: str
    institution_id: uuid.UUID | None = None
    status: str
    department: str | None = None
    reporting_to: uuid.UUID | None = None
    assigned_boards: list[Any] | None = None
    assigned_subjects: list[Any] | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")
    last_login_at: datetime | None = None
    last_login_ip: str | None = None
    login_count: int = 0
    is_active: bool = True
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    roles: list[RoleAssignmentItem] = Field(default_factory=list)

    model_config = {"from_attributes": True, "populate_by_name": True}


class RoleAssignmentItem(BaseModel):
    id: uuid.UUID
    role: str
    scope_type: str
    scope_id: uuid.UUID | None = None
    is_active: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str | None = None
    phone: str = Field(..., min_length=10, max_length=20)
    primary_role: str = "STUDENT"
    institution_id: uuid.UUID | None = None
    status: str = "ACTIVE"
    department: str | None = None
    reporting_to: uuid.UUID | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    avatar_url: str | None = None
    primary_role: str | None = None
    institution_id: uuid.UUID | None = None
    status: str | None = None
    department: str | None = None
    reporting_to: uuid.UUID | None = None
    assigned_boards: list[Any] | None = None
    assigned_subjects: list[Any] | None = None
    metadata_: dict[str, Any] | None = Field(None, alias="metadata")


class BlockRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    block: bool = True  # True to block, False to unblock


class RoleAssignRequest(BaseModel):
    role: str = Field(..., min_length=1)
    scope_type: str = "platform"
    scope_id: uuid.UUID | None = None


class ImpersonationLogItem(BaseModel):
    id: uuid.UUID
    admin_user_id: uuid.UUID
    admin_user_name: str | None = None
    target_user_id: uuid.UUID
    target_user_name: str | None = None
    reason: str | None = None
    ip_address: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    actions_taken: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ResponseSchema[PaginatedResponse[UserListItem]],
    summary="List users with filters",
)
async def list_users(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    role: str | None = Query(None),
    institution: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[UserListItem]]:
    """List users with filtering and pagination."""

    query = select(User).where(User.deleted_at.is_(None))
    count_query = (
        select(func.count()).select_from(User).where(User.deleted_at.is_(None))
    )

    if role:
        query = query.where(User.primary_role == role)
        count_query = count_query.where(User.primary_role == role)

    if institution:
        query = query.where(User.institution_id == institution)
        count_query = count_query.where(User.institution_id == institution)

    if status_filter:
        query = query.where(User.status == status_filter)
        count_query = count_query.where(User.status == status_filter)

    if search:
        search_filter = or_(
            User.full_name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.phone.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    items = [
        UserListItem(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            phone=u.phone,
            primary_role=u.primary_role,
            institution_id=u.institution_id,
            status=u.status.value if u.status else "",
            last_login_at=u.last_login_at,
            created_at=u.created_at,
        )
        for u in users
    ]

    paginated = PaginatedResponse[UserListItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


@router.post(
    "",
    response_model=ResponseSchema[UserDetail],
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
async def create_user(
    body: UserCreate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[UserDetail]:
    """Create a new user."""

    # Check for duplicate phone
    existing = await db.execute(select(User).where(User.phone == body.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with phone '{body.phone}' already exists",
        )

    user = User(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        primary_role=body.primary_role,
        institution_id=body.institution_id,
        status=body.status,
        department=body.department,
        reporting_to=body.reporting_to,
        metadata_=body.metadata_ or {},
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    detail = UserDetail(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        avatar_url=user.avatar_url,
        primary_role=user.primary_role,
        institution_id=user.institution_id,
        status=user.status.value if user.status else "",
        department=user.department,
        reporting_to=user.reporting_to,
        assigned_boards=user.assigned_boards,
        assigned_subjects=user.assigned_subjects,
        last_login_at=user.last_login_at,
        last_login_ip=user.last_login_ip,
        login_count=user.login_count,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=[],
    )
    return ResponseSchema(data=detail, message="User created successfully")


@router.get(
    "/platform-staff",
    response_model=ResponseSchema[PaginatedResponse[UserListItem]],
    summary="List platform staff",
)
async def list_platform_staff(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[UserListItem]]:
    """List platform-level staff users only."""

    base_filter = [
        User.primary_role.in_(PLATFORM_STAFF_ROLES),
        User.deleted_at.is_(None),
    ]

    count_query = select(func.count()).select_from(User).where(*base_filter)
    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        select(User)
        .where(*base_filter)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    users = result.scalars().all()

    items = [
        UserListItem(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            phone=u.phone,
            primary_role=u.primary_role,
            institution_id=u.institution_id,
            status=u.status.value if u.status else "",
            last_login_at=u.last_login_at,
            created_at=u.created_at,
        )
        for u in users
    ]

    paginated = PaginatedResponse[UserListItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


@router.get(
    "/impersonation-log",
    response_model=ResponseSchema[PaginatedResponse[ImpersonationLogItem]],
    summary="List impersonation logs",
)
async def list_impersonation_logs(
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[ImpersonationLogItem]]:
    """List impersonation session logs."""

    count_query = select(func.count()).select_from(ImpersonationLog)
    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        select(ImpersonationLog)
        .order_by(ImpersonationLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    items = [
        ImpersonationLogItem(
            id=log.id,
            admin_user_id=log.admin_user_id,
            admin_user_name=log.admin_user_name,
            target_user_id=log.target_user_id,
            target_user_name=log.target_user_name,
            reason=log.reason,
            ip_address=log.ip_address,
            started_at=log.started_at,
            ended_at=log.ended_at,
            actions_taken=log.actions_taken,
            created_at=log.created_at,
        )
        for log in logs
    ]

    paginated = PaginatedResponse[ImpersonationLogItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


@router.get(
    "/{user_id}",
    response_model=ResponseSchema[UserDetail],
    summary="Get user detail",
)
async def get_user(
    user_id: uuid.UUID,
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[UserDetail]:
    """Get detailed information about a specific user."""

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Fetch role assignments
    roles_result = await db.execute(
        select(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
    )
    role_assignments = roles_result.scalars().all()

    roles = [
        RoleAssignmentItem(
            id=ra.id,
            role=ra.role,
            scope_type=ra.scope_type,
            scope_id=ra.scope_id,
            is_active=ra.is_active,
            created_at=ra.created_at,
        )
        for ra in role_assignments
    ]

    detail = UserDetail(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        avatar_url=user.avatar_url,
        primary_role=user.primary_role,
        institution_id=user.institution_id,
        status=user.status.value if user.status else "",
        department=user.department,
        reporting_to=user.reporting_to,
        assigned_boards=user.assigned_boards,
        assigned_subjects=user.assigned_subjects,
        last_login_at=user.last_login_at,
        last_login_ip=user.last_login_ip,
        login_count=user.login_count,
        is_active=user.is_active,
        deleted_at=user.deleted_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=roles,
    )
    return ResponseSchema(data=detail)


@router.put(
    "/{user_id}",
    response_model=ResponseSchema[UserDetail],
    summary="Update user",
)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[UserDetail]:
    """Update an existing user."""

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = body.model_dump(exclude_unset=True, by_alias=False)
    for field_name, value in update_data.items():
        setattr(user, field_name, value)

    await db.flush()
    await db.refresh(user)

    # Fetch role assignments
    roles_result = await db.execute(
        select(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
    )
    role_assignments = roles_result.scalars().all()
    roles = [
        RoleAssignmentItem(
            id=ra.id,
            role=ra.role,
            scope_type=ra.scope_type,
            scope_id=ra.scope_id,
            is_active=ra.is_active,
            created_at=ra.created_at,
        )
        for ra in role_assignments
    ]

    detail = UserDetail(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        avatar_url=user.avatar_url,
        primary_role=user.primary_role,
        institution_id=user.institution_id,
        status=user.status.value if user.status else "",
        department=user.department,
        reporting_to=user.reporting_to,
        assigned_boards=user.assigned_boards,
        assigned_subjects=user.assigned_subjects,
        last_login_at=user.last_login_at,
        last_login_ip=user.last_login_ip,
        login_count=user.login_count,
        is_active=user.is_active,
        deleted_at=user.deleted_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=roles,
    )
    return ResponseSchema(data=detail, message="User updated successfully")


@router.post(
    "/{user_id}/block",
    response_model=ResponseSchema[None],
    summary="Block or unblock user",
)
async def block_user(
    user_id: uuid.UUID,
    body: BlockRequest,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[None]:
    """Block or unblock a user."""

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if body.block:
        user.status = UserStatus.BLOCKED
        user.is_active = False
        message = "User blocked successfully"
    else:
        user.status = UserStatus.ACTIVE
        user.is_active = True
        message = "User unblocked successfully"

    await db.flush()
    return ResponseSchema(message=message)


@router.post(
    "/{user_id}/roles",
    response_model=ResponseSchema[RoleAssignmentItem],
    status_code=status.HTTP_201_CREATED,
    summary="Assign role to user",
)
async def assign_role(
    user_id: uuid.UUID,
    body: RoleAssignRequest,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[RoleAssignmentItem]:
    """Assign a role to a user."""

    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check if role assignment already exists
    existing = await db.execute(
        select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role == body.role,
            UserRoleAssignment.scope_type == body.scope_type,
            UserRoleAssignment.scope_id == body.scope_id,
            UserRoleAssignment.is_active.is_(True),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role assignment already exists for this user",
        )

    assignment = UserRoleAssignment(
        user_id=user_id,
        role=body.role,
        scope_type=body.scope_type,
        scope_id=body.scope_id,
        assigned_by=current_user.user_id,
    )
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)

    item = RoleAssignmentItem(
        id=assignment.id,
        role=assignment.role,
        scope_type=assignment.scope_type,
        scope_id=assignment.scope_id,
        is_active=assignment.is_active,
        created_at=assignment.created_at,
    )
    return ResponseSchema(data=item, message="Role assigned successfully")
