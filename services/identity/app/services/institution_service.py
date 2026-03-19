import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InstitutionNotFoundError
from app.models.institution import Institution
from app.schemas.institution import InstitutionCreate, InstitutionUpdate


async def create_institution(db: AsyncSession, data: InstitutionCreate) -> Institution:
    institution = Institution(
        name=data.name,
        code=data.code,
        portal_type=data.portal_type,
        subscription_plan=data.subscription_plan,
        settings=data.settings,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        address=data.address,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
    )
    db.add(institution)
    await db.flush()
    await db.refresh(institution)
    return institution


async def get_institution_by_id(db: AsyncSession, institution_id: uuid.UUID) -> Institution:
    result = await db.execute(
        select(Institution).where(Institution.id == institution_id)
    )
    institution = result.scalar_one_or_none()
    if institution is None:
        raise InstitutionNotFoundError()
    return institution


async def update_institution(
    db: AsyncSession, institution_id: uuid.UUID, data: InstitutionUpdate
) -> Institution:
    institution = await get_institution_by_id(db, institution_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(institution, field, value)
    await db.flush()
    await db.refresh(institution)
    return institution


async def list_institutions(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    is_active: bool | None = None,
) -> dict:
    from sqlalchemy import func
    import math

    query = select(Institution)
    count_query = select(func.count(Institution.id))

    if is_active is not None:
        query = query.where(Institution.is_active == is_active)
        count_query = count_query.where(Institution.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Institution.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    institutions = result.scalars().all()

    return {
        "items": institutions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total > 0 else 0,
    }
