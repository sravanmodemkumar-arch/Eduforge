import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Get the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile. Non-staff users cannot change role or is_active."""
    # Restrict fields for non-staff users
    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.INSTITUTION_ADMIN, UserRole.STAFF):
        body.role = None
        body.is_active = None
        body.institution_id = None

    user = await user_service.update_user(db, current_user.id, body)
    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "INSTITUTION_ADMIN", "STAFF"))],
)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a user by ID (staff only)."""
    user = await user_service.get_user_by_id(db, user_id)
    return UserResponse.model_validate(user)


@router.get(
    "/",
    response_model=UserListResponse,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "INSTITUTION_ADMIN", "STAFF"))],
)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: UserRole | None = None,
    institution_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List users with pagination and filters (staff only)."""
    return await user_service.list_users(
        db,
        page=page,
        page_size=page_size,
        role=role,
        institution_id=institution_id,
        is_active=is_active,
        search=search,
    )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "INSTITUTION_ADMIN", "STAFF"))],
)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (staff only)."""
    user = await user_service.create_user(db, body)
    return UserResponse.model_validate(user)
