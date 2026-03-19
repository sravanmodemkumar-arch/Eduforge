"""Super Admin Institution Management API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.institution import (
    Institution,
    InstitutionGroup,
    InstitutionStatus,
    InstitutionType,
    SubscriptionPlan,
)
from app.models.user import User
from shared.auth.dependencies import UserToken
from shared.schemas.common import PaginatedResponse, ResponseSchema

from .dependencies import require_admin, require_super_admin

router = APIRouter(prefix="/institutions", tags=["SA › Institutions"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class InstitutionListItem(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    institution_type: str
    status: str
    subscription_plan: str | None = None
    subscription_status: str | None = None
    city: str | None = None
    state: str | None = None
    health_score: int | None = None
    group_id: uuid.UUID | None = None
    total_users: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class InstitutionDetail(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    institution_type: str
    status: str
    group_id: uuid.UUID | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    custom_domain: str | None = None
    subscription_plan: str | None = None
    subscription_status: str | None = None
    subscription_start: datetime | None = None
    subscription_expiry: datetime | None = None
    subscription_amount: float | None = None
    auto_renew: bool = True
    billing_cycle: str | None = None
    max_students: int = 100
    max_storage_gb: int = 1
    api_rate_limit: int = 100
    features_enabled: dict[str, Any] | None = None
    health_score: int | None = None
    last_admin_login: datetime | None = None
    onboarding_stage: str | None = None
    settings: dict[str, Any] | None = None
    tags: list[Any] | None = None
    internal_notes: list[Any] | None = None
    is_active: bool = True
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    # Aggregated stats
    total_users: int = 0
    total_students: int = 0
    total_teachers: int = 0

    model_config = {"from_attributes": True}


class InstitutionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    institution_type: str
    status: str = "PENDING_SETUP"
    group_id: uuid.UUID | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    logo_url: str | None = None
    subscription_plan: str | None = None
    max_students: int = 100
    max_storage_gb: int = 1
    settings: dict[str, Any] | None = None
    tags: list[Any] | None = None


class InstitutionUpdate(BaseModel):
    name: str | None = None
    institution_type: str | None = None
    status: str | None = None
    group_id: uuid.UUID | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    custom_domain: str | None = None
    subscription_plan: str | None = None
    subscription_status: str | None = None
    subscription_expiry: datetime | None = None
    subscription_amount: float | None = None
    auto_renew: bool | None = None
    billing_cycle: str | None = None
    max_students: int | None = None
    max_storage_gb: int | None = None
    api_rate_limit: int | None = None
    features_enabled: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None
    tags: list[Any] | None = None
    internal_notes: list[Any] | None = None


class SuspendRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class GroupListItem(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    group_type: str
    is_active: bool
    institution_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    group_type: str = "UNIVERSITY"
    owner_user_id: uuid.UUID | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    subscription_plan: str | None = None
    subscription_amount: float | None = None
    settings: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ResponseSchema[PaginatedResponse[InstitutionListItem]],
    summary="List institutions with filters",
)
async def list_institutions(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    # Filters
    institution_type: str | None = Query(None, alias="type"),
    status_filter: str | None = Query(None, alias="status"),
    plan: str | None = Query(None),
    state: str | None = Query(None),
    city: str | None = Query(None),
    health: str | None = Query(None, description="low, medium, high"),
    group: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[InstitutionListItem]]:
    """List institutions with comprehensive filtering and pagination."""

    query = select(Institution).where(Institution.deleted_at.is_(None))
    count_query = (
        select(func.count())
        .select_from(Institution)
        .where(Institution.deleted_at.is_(None))
    )

    # Apply filters
    if institution_type:
        query = query.where(Institution.institution_type == institution_type)
        count_query = count_query.where(Institution.institution_type == institution_type)

    if status_filter:
        query = query.where(Institution.status == status_filter)
        count_query = count_query.where(Institution.status == status_filter)

    if plan:
        query = query.where(Institution.subscription_plan == plan)
        count_query = count_query.where(Institution.subscription_plan == plan)

    if state:
        query = query.where(Institution.state.ilike(f"%{state}%"))
        count_query = count_query.where(Institution.state.ilike(f"%{state}%"))

    if city:
        query = query.where(Institution.city.ilike(f"%{city}%"))
        count_query = count_query.where(Institution.city.ilike(f"%{city}%"))

    if health:
        if health == "low":
            query = query.where(Institution.health_score < 40)
            count_query = count_query.where(Institution.health_score < 40)
        elif health == "medium":
            query = query.where(
                Institution.health_score >= 40, Institution.health_score < 70
            )
            count_query = count_query.where(
                Institution.health_score >= 40, Institution.health_score < 70
            )
        elif health == "high":
            query = query.where(Institution.health_score >= 70)
            count_query = count_query.where(Institution.health_score >= 70)

    if group:
        query = query.where(Institution.group_id == group)
        count_query = count_query.where(Institution.group_id == group)

    if search:
        search_filter = or_(
            Institution.name.ilike(f"%{search}%"),
            Institution.code.ilike(f"%{search}%"),
            Institution.contact_email.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Total count
    total = (await db.execute(count_query)).scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    query = query.order_by(Institution.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    institutions = result.scalars().all()

    # Build response items with user counts
    items: list[InstitutionListItem] = []
    for inst in institutions:
        user_count_result = await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.institution_id == inst.id, User.deleted_at.is_(None))
        )
        total_users = user_count_result.scalar_one()

        items.append(
            InstitutionListItem(
                id=inst.id,
                name=inst.name,
                code=inst.code,
                institution_type=inst.institution_type.value if inst.institution_type else "",
                status=inst.status.value if inst.status else "",
                subscription_plan=(
                    inst.subscription_plan.value if inst.subscription_plan else None
                ),
                subscription_status=(
                    inst.subscription_status.value if inst.subscription_status else None
                ),
                city=inst.city,
                state=inst.state,
                health_score=inst.health_score,
                group_id=inst.group_id,
                total_users=total_users,
                created_at=inst.created_at,
            )
        )

    paginated = PaginatedResponse[InstitutionListItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


@router.post(
    "",
    response_model=ResponseSchema[InstitutionDetail],
    status_code=status.HTTP_201_CREATED,
    summary="Create institution",
)
async def create_institution(
    body: InstitutionCreate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[InstitutionDetail]:
    """Create a new institution."""

    # Check for duplicate code
    existing = await db.execute(
        select(Institution).where(Institution.code == body.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Institution with code '{body.code}' already exists",
        )

    institution = Institution(
        name=body.name,
        code=body.code,
        institution_type=body.institution_type,
        status=body.status,
        group_id=body.group_id,
        contact_name=body.contact_name,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone,
        address=body.address,
        city=body.city,
        state=body.state,
        pincode=body.pincode,
        logo_url=body.logo_url,
        subscription_plan=body.subscription_plan,
        max_students=body.max_students,
        max_storage_gb=body.max_storage_gb,
        settings=body.settings or {},
        tags=body.tags or [],
    )
    db.add(institution)
    await db.flush()
    await db.refresh(institution)

    detail = InstitutionDetail(
        id=institution.id,
        name=institution.name,
        code=institution.code,
        institution_type=institution.institution_type.value if institution.institution_type else "",
        status=institution.status.value if institution.status else "",
        group_id=institution.group_id,
        contact_name=institution.contact_name,
        contact_email=institution.contact_email,
        contact_phone=institution.contact_phone,
        address=institution.address,
        city=institution.city,
        state=institution.state,
        pincode=institution.pincode,
        logo_url=institution.logo_url,
        subscription_plan=(
            institution.subscription_plan.value if institution.subscription_plan else None
        ),
        max_students=institution.max_students,
        max_storage_gb=institution.max_storage_gb,
        settings=institution.settings,
        tags=institution.tags,
        is_active=institution.is_active,
        created_at=institution.created_at,
        updated_at=institution.updated_at,
    )
    return ResponseSchema(data=detail, message="Institution created successfully")


@router.get(
    "/{institution_id}",
    response_model=ResponseSchema[InstitutionDetail],
    summary="Get institution detail",
)
async def get_institution(
    institution_id: uuid.UUID,
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[InstitutionDetail]:
    """Get detailed information about a specific institution including stats."""

    result = await db.execute(
        select(Institution).where(Institution.id == institution_id)
    )
    institution = result.scalar_one_or_none()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found",
        )

    # Aggregate user stats
    total_users_result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.institution_id == institution_id, User.deleted_at.is_(None))
    )
    total_users = total_users_result.scalar_one()

    total_students_result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.institution_id == institution_id,
            User.primary_role == "STUDENT",
            User.deleted_at.is_(None),
        )
    )
    total_students = total_students_result.scalar_one()

    total_teachers_result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.institution_id == institution_id,
            User.primary_role == "TEACHER",
            User.deleted_at.is_(None),
        )
    )
    total_teachers = total_teachers_result.scalar_one()

    detail = InstitutionDetail(
        id=institution.id,
        name=institution.name,
        code=institution.code,
        institution_type=institution.institution_type.value if institution.institution_type else "",
        status=institution.status.value if institution.status else "",
        group_id=institution.group_id,
        contact_name=institution.contact_name,
        contact_email=institution.contact_email,
        contact_phone=institution.contact_phone,
        address=institution.address,
        city=institution.city,
        state=institution.state,
        pincode=institution.pincode,
        logo_url=institution.logo_url,
        primary_color=institution.primary_color,
        secondary_color=institution.secondary_color,
        custom_domain=institution.custom_domain,
        subscription_plan=(
            institution.subscription_plan.value if institution.subscription_plan else None
        ),
        subscription_status=(
            institution.subscription_status.value if institution.subscription_status else None
        ),
        subscription_start=institution.subscription_start,
        subscription_expiry=institution.subscription_expiry,
        subscription_amount=institution.subscription_amount,
        auto_renew=institution.auto_renew,
        billing_cycle=institution.billing_cycle,
        max_students=institution.max_students,
        max_storage_gb=institution.max_storage_gb,
        api_rate_limit=institution.api_rate_limit,
        features_enabled=institution.features_enabled,
        health_score=institution.health_score,
        last_admin_login=institution.last_admin_login,
        onboarding_stage=institution.onboarding_stage,
        settings=institution.settings,
        tags=institution.tags,
        internal_notes=institution.internal_notes,
        is_active=institution.is_active,
        deleted_at=institution.deleted_at,
        created_at=institution.created_at,
        updated_at=institution.updated_at,
        total_users=total_users,
        total_students=total_students,
        total_teachers=total_teachers,
    )
    return ResponseSchema(data=detail)


@router.put(
    "/{institution_id}",
    response_model=ResponseSchema[InstitutionDetail],
    summary="Update institution",
)
async def update_institution(
    institution_id: uuid.UUID,
    body: InstitutionUpdate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[InstitutionDetail]:
    """Update an existing institution."""

    result = await db.execute(
        select(Institution).where(Institution.id == institution_id)
    )
    institution = result.scalar_one_or_none()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(institution, field_name, value)

    await db.flush()
    await db.refresh(institution)

    detail = InstitutionDetail(
        id=institution.id,
        name=institution.name,
        code=institution.code,
        institution_type=institution.institution_type.value if institution.institution_type else "",
        status=institution.status.value if institution.status else "",
        group_id=institution.group_id,
        contact_name=institution.contact_name,
        contact_email=institution.contact_email,
        contact_phone=institution.contact_phone,
        address=institution.address,
        city=institution.city,
        state=institution.state,
        pincode=institution.pincode,
        logo_url=institution.logo_url,
        primary_color=institution.primary_color,
        secondary_color=institution.secondary_color,
        custom_domain=institution.custom_domain,
        subscription_plan=(
            institution.subscription_plan.value if institution.subscription_plan else None
        ),
        subscription_status=(
            institution.subscription_status.value if institution.subscription_status else None
        ),
        subscription_start=institution.subscription_start,
        subscription_expiry=institution.subscription_expiry,
        subscription_amount=institution.subscription_amount,
        auto_renew=institution.auto_renew,
        billing_cycle=institution.billing_cycle,
        max_students=institution.max_students,
        max_storage_gb=institution.max_storage_gb,
        api_rate_limit=institution.api_rate_limit,
        features_enabled=institution.features_enabled,
        health_score=institution.health_score,
        last_admin_login=institution.last_admin_login,
        onboarding_stage=institution.onboarding_stage,
        settings=institution.settings,
        tags=institution.tags,
        internal_notes=institution.internal_notes,
        is_active=institution.is_active,
        deleted_at=institution.deleted_at,
        created_at=institution.created_at,
        updated_at=institution.updated_at,
    )
    return ResponseSchema(data=detail, message="Institution updated successfully")


@router.delete(
    "/{institution_id}",
    response_model=ResponseSchema[None],
    summary="Soft delete institution",
)
async def delete_institution(
    institution_id: uuid.UUID,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[None]:
    """Soft-delete an institution (sets deleted_at timestamp)."""

    result = await db.execute(
        select(Institution).where(
            Institution.id == institution_id,
            Institution.deleted_at.is_(None),
        )
    )
    institution = result.scalar_one_or_none()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found",
        )

    institution.deleted_at = datetime.now(timezone.utc)
    institution.status = InstitutionStatus.DELETED
    institution.is_active = False
    await db.flush()

    return ResponseSchema(message="Institution deleted successfully")


@router.post(
    "/{institution_id}/suspend",
    response_model=ResponseSchema[None],
    summary="Suspend institution",
)
async def suspend_institution(
    institution_id: uuid.UUID,
    body: SuspendRequest,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[None]:
    """Suspend an institution with a reason."""

    result = await db.execute(
        select(Institution).where(
            Institution.id == institution_id,
            Institution.deleted_at.is_(None),
        )
    )
    institution = result.scalar_one_or_none()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found",
        )

    institution.status = InstitutionStatus.SUSPENDED
    # Store suspension reason in internal notes
    notes = institution.internal_notes or []
    notes.append(
        {
            "type": "suspension",
            "reason": body.reason,
            "by": str(current_user.user_id),
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    institution.internal_notes = notes
    await db.flush()

    return ResponseSchema(message="Institution suspended successfully")


@router.post(
    "/{institution_id}/restore",
    response_model=ResponseSchema[None],
    summary="Restore institution from trash",
)
async def restore_institution(
    institution_id: uuid.UUID,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[None]:
    """Restore a soft-deleted institution."""

    result = await db.execute(
        select(Institution).where(Institution.id == institution_id)
    )
    institution = result.scalar_one_or_none()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found",
        )

    if institution.deleted_at is None and institution.status != InstitutionStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution is not in deleted state",
        )

    institution.deleted_at = None
    institution.status = InstitutionStatus.ACTIVE
    institution.is_active = True
    await db.flush()

    return ResponseSchema(message="Institution restored successfully")


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------


@router.get(
    "/groups",
    response_model=ResponseSchema[list[GroupListItem]],
    summary="List institution groups",
)
async def list_groups(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[list[GroupListItem]]:
    """List all institution groups (universities, chains, etc.)."""

    result = await db.execute(
        select(InstitutionGroup).order_by(InstitutionGroup.created_at.desc())
    )
    groups = result.scalars().all()

    items: list[GroupListItem] = []
    for grp in groups:
        inst_count_result = await db.execute(
            select(func.count())
            .select_from(Institution)
            .where(Institution.group_id == grp.id, Institution.deleted_at.is_(None))
        )
        inst_count = inst_count_result.scalar_one()

        items.append(
            GroupListItem(
                id=grp.id,
                name=grp.name,
                code=grp.code,
                group_type=grp.group_type,
                is_active=grp.is_active,
                institution_count=inst_count,
                created_at=grp.created_at,
            )
        )

    return ResponseSchema(data=items)


@router.post(
    "/groups",
    response_model=ResponseSchema[GroupListItem],
    status_code=status.HTTP_201_CREATED,
    summary="Create institution group",
)
async def create_group(
    body: GroupCreate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[GroupListItem]:
    """Create a new institution group."""

    # Check for duplicate code
    existing = await db.execute(
        select(InstitutionGroup).where(InstitutionGroup.code == body.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Group with code '{body.code}' already exists",
        )

    group = InstitutionGroup(
        name=body.name,
        code=body.code,
        group_type=body.group_type,
        owner_user_id=body.owner_user_id,
        contact_name=body.contact_name,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone,
        subscription_plan=body.subscription_plan,
        subscription_amount=body.subscription_amount,
        settings=body.settings or {},
    )
    db.add(group)
    await db.flush()
    await db.refresh(group)

    item = GroupListItem(
        id=group.id,
        name=group.name,
        code=group.code,
        group_type=group.group_type,
        is_active=group.is_active,
        institution_count=0,
        created_at=group.created_at,
    )
    return ResponseSchema(data=item, message="Group created successfully")
