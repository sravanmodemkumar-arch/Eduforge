"""Super Admin System Configuration & Feature Flags API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.superadmin import ConfigHistory, FeatureFlag, SystemConfig
from shared.auth.dependencies import UserToken
from shared.schemas.common import PaginatedResponse, ResponseSchema

from .dependencies import require_admin, require_super_admin

router = APIRouter(tags=["SA › Configuration"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ConfigItem(BaseModel):
    id: uuid.UUID
    key: str
    value: str | None = None
    value_type: str = "string"
    category: str = "general"
    description: str | None = None
    is_sensitive: bool = False
    updated_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConfigUpdate(BaseModel):
    value: str
    description: str | None = None


class ConfigHistoryItem(BaseModel):
    id: uuid.UUID
    config_key: str
    old_value: str | None = None
    new_value: str | None = None
    changed_by: uuid.UUID | None = None
    changed_by_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FeatureFlagItem(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    description: str | None = None
    status: str = "OFF"
    rollout_percentage: int = 0
    target_institutions: list[Any] | None = None
    auto_enable_date: datetime | None = None
    updated_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FeatureFlagCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    status: str = "OFF"
    rollout_percentage: int = Field(0, ge=0, le=100)
    target_institutions: list[Any] | None = None
    auto_enable_date: datetime | None = None


class FeatureFlagUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    rollout_percentage: int | None = Field(None, ge=0, le=100)
    target_institutions: list[Any] | None = None
    auto_enable_date: datetime | None = None


# ---------------------------------------------------------------------------
# Config Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/config",
    response_model=ResponseSchema[list[ConfigItem]],
    summary="List all config entries",
)
async def list_config(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    category: str | None = Query(None),
) -> ResponseSchema[list[ConfigItem]]:
    """List all system configuration entries."""

    query = select(SystemConfig).order_by(SystemConfig.category, SystemConfig.key)
    if category:
        query = query.where(SystemConfig.category == category)

    result = await db.execute(query)
    configs = result.scalars().all()

    items = [
        ConfigItem(
            id=c.id,
            key=c.key,
            value=c.value if not c.is_sensitive else "********",
            value_type=c.value_type,
            category=c.category,
            description=c.description,
            is_sensitive=c.is_sensitive,
            updated_by=c.updated_by,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in configs
    ]
    return ResponseSchema(data=items)


@router.put(
    "/config/{key}",
    response_model=ResponseSchema[ConfigItem],
    summary="Update config value",
)
async def update_config(
    key: str,
    body: ConfigUpdate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[ConfigItem]:
    """Update a system configuration value. Changes are logged to history."""

    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Config key '{key}' not found",
        )

    old_value = config.value

    # Log change to history
    history_entry = ConfigHistory(
        config_key=key,
        old_value=old_value,
        new_value=body.value,
        changed_by=current_user.user_id,
    )
    db.add(history_entry)

    # Update config
    config.value = body.value
    if body.description is not None:
        config.description = body.description
    config.updated_by = current_user.user_id

    await db.flush()
    await db.refresh(config)

    item = ConfigItem(
        id=config.id,
        key=config.key,
        value=config.value if not config.is_sensitive else "********",
        value_type=config.value_type,
        category=config.category,
        description=config.description,
        is_sensitive=config.is_sensitive,
        updated_by=config.updated_by,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )
    return ResponseSchema(data=item, message="Config updated successfully")


@router.get(
    "/config/history",
    response_model=ResponseSchema[PaginatedResponse[ConfigHistoryItem]],
    summary="Config change history",
)
async def get_config_history(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    config_key: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ResponseSchema[PaginatedResponse[ConfigHistoryItem]]:
    """List configuration change history."""

    from sqlalchemy import func

    query = select(ConfigHistory)
    count_query = select(func.count()).select_from(ConfigHistory)

    if config_key:
        query = query.where(ConfigHistory.config_key == config_key)
        count_query = count_query.where(ConfigHistory.config_key == config_key)

    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * page_size
    query = (
        query.order_by(ConfigHistory.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    entries = result.scalars().all()

    items = [
        ConfigHistoryItem(
            id=e.id,
            config_key=e.config_key,
            old_value=e.old_value,
            new_value=e.new_value,
            changed_by=e.changed_by,
            changed_by_name=e.changed_by_name,
            created_at=e.created_at,
        )
        for e in entries
    ]

    paginated = PaginatedResponse[ConfigHistoryItem](
        items=items, total=total, page=page, page_size=page_size
    )
    return ResponseSchema(data=paginated)


# ---------------------------------------------------------------------------
# Feature Flag Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/feature-flags",
    response_model=ResponseSchema[list[FeatureFlagItem]],
    summary="List feature flags",
)
async def list_feature_flags(
    current_user: UserToken = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[list[FeatureFlagItem]]:
    """List all feature flags."""

    result = await db.execute(
        select(FeatureFlag).order_by(FeatureFlag.key)
    )
    flags = result.scalars().all()

    items = [
        FeatureFlagItem(
            id=f.id,
            key=f.key,
            name=f.name,
            description=f.description,
            status=f.status,
            rollout_percentage=f.rollout_percentage,
            target_institutions=f.target_institutions,
            auto_enable_date=f.auto_enable_date,
            updated_by=f.updated_by,
            created_at=f.created_at,
            updated_at=f.updated_at,
        )
        for f in flags
    ]
    return ResponseSchema(data=items)


@router.post(
    "/feature-flags",
    response_model=ResponseSchema[FeatureFlagItem],
    status_code=status.HTTP_201_CREATED,
    summary="Create feature flag",
)
async def create_feature_flag(
    body: FeatureFlagCreate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[FeatureFlagItem]:
    """Create a new feature flag."""

    # Check for duplicate key
    existing = await db.execute(
        select(FeatureFlag).where(FeatureFlag.key == body.key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Feature flag with key '{body.key}' already exists",
        )

    flag = FeatureFlag(
        key=body.key,
        name=body.name,
        description=body.description,
        status=body.status,
        rollout_percentage=body.rollout_percentage,
        target_institutions=body.target_institutions or [],
        auto_enable_date=body.auto_enable_date,
        updated_by=current_user.user_id,
    )
    db.add(flag)
    await db.flush()
    await db.refresh(flag)

    item = FeatureFlagItem(
        id=flag.id,
        key=flag.key,
        name=flag.name,
        description=flag.description,
        status=flag.status,
        rollout_percentage=flag.rollout_percentage,
        target_institutions=flag.target_institutions,
        auto_enable_date=flag.auto_enable_date,
        updated_by=flag.updated_by,
        created_at=flag.created_at,
        updated_at=flag.updated_at,
    )
    return ResponseSchema(data=item, message="Feature flag created successfully")


@router.put(
    "/feature-flags/{flag_id}",
    response_model=ResponseSchema[FeatureFlagItem],
    summary="Update feature flag",
)
async def update_feature_flag(
    flag_id: uuid.UUID,
    body: FeatureFlagUpdate,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[FeatureFlagItem]:
    """Update an existing feature flag."""

    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.id == flag_id)
    )
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature flag not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(flag, field_name, value)
    flag.updated_by = current_user.user_id

    await db.flush()
    await db.refresh(flag)

    item = FeatureFlagItem(
        id=flag.id,
        key=flag.key,
        name=flag.name,
        description=flag.description,
        status=flag.status,
        rollout_percentage=flag.rollout_percentage,
        target_institutions=flag.target_institutions,
        auto_enable_date=flag.auto_enable_date,
        updated_by=flag.updated_by,
        created_at=flag.created_at,
        updated_at=flag.updated_at,
    )
    return ResponseSchema(data=item, message="Feature flag updated successfully")
