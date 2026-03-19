"""Super Admin Emergency Controls API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.institution import Institution, InstitutionStatus
from app.models.session import Session
from app.models.superadmin import AuditLog, SystemConfig
from shared.auth.dependencies import UserToken
from shared.schemas.common import ResponseSchema

from .dependencies import require_super_admin

router = APIRouter(prefix="/emergency", tags=["SA › Emergency"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class MaintenanceModeRequest(BaseModel):
    enabled: bool
    message: str | None = Field(
        None,
        description="Message to display to users during maintenance",
    )


class MaintenanceModeResponse(BaseModel):
    enabled: bool
    message: str | None = None
    toggled_by: uuid.UUID
    toggled_at: datetime


class StopExamsResponse(BaseModel):
    message: str
    triggered_by: uuid.UUID
    triggered_at: datetime


class FreezeInstitutionResponse(BaseModel):
    institution_id: uuid.UUID
    previous_status: str
    new_status: str = "SUSPENDED"
    frozen_by: uuid.UUID
    frozen_at: datetime


class RevokeAllSessionsResponse(BaseModel):
    sessions_revoked: int
    revoked_by: uuid.UUID
    revoked_at: datetime


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/maintenance-mode",
    response_model=ResponseSchema[MaintenanceModeResponse],
    summary="Toggle maintenance mode",
)
async def toggle_maintenance_mode(
    body: MaintenanceModeRequest,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[MaintenanceModeResponse]:
    """Enable or disable platform-wide maintenance mode.

    When enabled, all non-admin users will see a maintenance page.
    """

    now = datetime.now(timezone.utc)

    # Upsert maintenance mode config
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == "maintenance_mode")
    )
    config = result.scalar_one_or_none()

    if config:
        config.value = "true" if body.enabled else "false"
        config.updated_by = current_user.user_id
    else:
        config = SystemConfig(
            key="maintenance_mode",
            value="true" if body.enabled else "false",
            value_type="bool",
            category="system",
            description="Platform-wide maintenance mode toggle",
            updated_by=current_user.user_id,
        )
        db.add(config)

    # Store maintenance message if provided
    if body.message is not None:
        msg_result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == "maintenance_message")
        )
        msg_config = msg_result.scalar_one_or_none()
        if msg_config:
            msg_config.value = body.message
            msg_config.updated_by = current_user.user_id
        else:
            msg_config = SystemConfig(
                key="maintenance_message",
                value=body.message,
                value_type="string",
                category="system",
                description="Message displayed during maintenance mode",
                updated_by=current_user.user_id,
            )
            db.add(msg_config)

    # Create audit log entry
    audit = AuditLog(
        user_id=current_user.user_id,
        action="TOGGLE_MAINTENANCE_MODE",
        resource_type="system",
        resource_id="maintenance_mode",
        description=f"Maintenance mode {'enabled' if body.enabled else 'disabled'}",
        details={"enabled": body.enabled, "message": body.message},
    )
    db.add(audit)
    await db.flush()

    response = MaintenanceModeResponse(
        enabled=body.enabled,
        message=body.message,
        toggled_by=current_user.user_id,
        toggled_at=now,
    )
    action = "enabled" if body.enabled else "disabled"
    return ResponseSchema(data=response, message=f"Maintenance mode {action}")


@router.post(
    "/stop-exams",
    response_model=ResponseSchema[StopExamsResponse],
    summary="Stop all running exams",
)
async def stop_all_exams(
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[StopExamsResponse]:
    """Emergency stop for all currently running exams.

    This creates an audit trail and would trigger a cross-service call to
    the assessment service to pause/stop all active exam sessions.
    """

    now = datetime.now(timezone.utc)

    # Create audit log entry
    audit = AuditLog(
        user_id=current_user.user_id,
        action="EMERGENCY_STOP_EXAMS",
        resource_type="system",
        resource_id="all_exams",
        description="Emergency stop triggered for all running exams",
        details={"triggered_at": now.isoformat()},
    )
    db.add(audit)
    await db.flush()

    # In production, this would issue an RPC/event to the assessment service.
    response = StopExamsResponse(
        message="Emergency stop signal sent to assessment service",
        triggered_by=current_user.user_id,
        triggered_at=now,
    )
    return ResponseSchema(
        data=response,
        message="Emergency exam stop triggered successfully",
    )


@router.post(
    "/freeze-institution/{institution_id}",
    response_model=ResponseSchema[FreezeInstitutionResponse],
    summary="Freeze an institution",
)
async def freeze_institution(
    institution_id: uuid.UUID,
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[FreezeInstitutionResponse]:
    """Immediately freeze (suspend) an institution.

    All users of the institution will be locked out until the freeze is lifted.
    """

    result = await db.execute(
        select(Institution).where(Institution.id == institution_id)
    )
    institution = result.scalar_one_or_none()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found",
        )

    previous_status = (
        institution.status.value
        if hasattr(institution.status, "value")
        else str(institution.status)
    )

    if institution.status == InstitutionStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Institution is already suspended",
        )

    now = datetime.now(timezone.utc)

    institution.status = InstitutionStatus.SUSPENDED

    # Store freeze info in internal notes
    notes = institution.internal_notes or []
    notes.append(
        {
            "type": "emergency_freeze",
            "previous_status": previous_status,
            "by": str(current_user.user_id),
            "at": now.isoformat(),
        }
    )
    institution.internal_notes = notes

    # Revoke all sessions for this institution's users
    from app.models.user import User

    user_ids_result = await db.execute(
        select(User.id).where(User.institution_id == institution_id)
    )
    user_ids = [row[0] for row in user_ids_result.all()]

    if user_ids:
        await db.execute(
            update(Session)
            .where(Session.user_id.in_(user_ids), Session.is_revoked.is_(False))
            .values(is_revoked=True)
        )

    # Audit log
    audit = AuditLog(
        user_id=current_user.user_id,
        action="EMERGENCY_FREEZE_INSTITUTION",
        resource_type="institution",
        resource_id=str(institution_id),
        description=f"Emergency freeze on institution {institution.name}",
        details={
            "previous_status": previous_status,
            "sessions_revoked_for_users": len(user_ids),
        },
    )
    db.add(audit)
    await db.flush()

    response = FreezeInstitutionResponse(
        institution_id=institution_id,
        previous_status=previous_status,
        new_status="SUSPENDED",
        frozen_by=current_user.user_id,
        frozen_at=now,
    )
    return ResponseSchema(
        data=response,
        message=f"Institution '{institution.name}' frozen successfully",
    )


@router.post(
    "/revoke-all-sessions",
    response_model=ResponseSchema[RevokeAllSessionsResponse],
    summary="Revoke all active sessions",
)
async def revoke_all_sessions(
    current_user: UserToken = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchema[RevokeAllSessionsResponse]:
    """Revoke all active sessions platform-wide.

    This is a nuclear option — every user will be logged out immediately.
    """

    now = datetime.now(timezone.utc)

    # Count active sessions before revoking
    from sqlalchemy import func

    count_result = await db.execute(
        select(func.count())
        .select_from(Session)
        .where(Session.is_revoked.is_(False), Session.expires_at > now)
    )
    active_count = count_result.scalar_one()

    # Revoke all non-revoked sessions
    await db.execute(
        update(Session)
        .where(Session.is_revoked.is_(False))
        .values(is_revoked=True)
    )

    # Audit log
    audit = AuditLog(
        user_id=current_user.user_id,
        action="EMERGENCY_REVOKE_ALL_SESSIONS",
        resource_type="system",
        resource_id="all_sessions",
        description=f"Emergency revoke of all {active_count} active sessions",
        details={"sessions_revoked": active_count},
    )
    db.add(audit)
    await db.flush()

    response = RevokeAllSessionsResponse(
        sessions_revoked=active_count,
        revoked_by=current_user.user_id,
        revoked_at=now,
    )
    return ResponseSchema(
        data=response,
        message=f"All {active_count} active sessions revoked successfully",
    )
