import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.schemas.institution import (
    InstitutionCreate,
    InstitutionResponse,
    InstitutionUpdate,
)
from app.services import institution_service

router = APIRouter(prefix="/api/v1/institutions", tags=["Institutions"])


@router.post("/", response_model=InstitutionResponse, status_code=201)
async def register_institution(
    body: InstitutionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new institution."""
    institution = await institution_service.create_institution(db, body)
    return InstitutionResponse.model_validate(institution)


@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(
    institution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get an institution by ID."""
    institution = await institution_service.get_institution_by_id(db, institution_id)
    return InstitutionResponse.model_validate(institution)


@router.put("/{institution_id}", response_model=InstitutionResponse)
async def update_institution(
    institution_id: uuid.UUID,
    body: InstitutionUpdate,
    current_user: User = Depends(
        require_roles("SUPER_ADMIN", "INSTITUTION_ADMIN")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Update an institution (admin only)."""
    institution = await institution_service.update_institution(db, institution_id, body)
    return InstitutionResponse.model_validate(institution)


@router.get(
    "/",
    dependencies=[Depends(require_roles("SUPER_ADMIN"))],
)
async def list_institutions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all institutions (super admin only)."""
    result = await institution_service.list_institutions(
        db, page=page, page_size=page_size, is_active=is_active
    )
    return {
        "items": [InstitutionResponse.model_validate(i) for i in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "pages": result["pages"],
    }
