"""Models for Super Admin features — audit, config, feature flags, incidents, etc."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_identity_audit_user", "user_id"),
        Index("ix_identity_audit_action", "action"),
        Index("ix_identity_audit_resource", "resource_type", "resource_id"),
        Index("ix_identity_audit_created", "created_at"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    user_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # Before/after snapshots for update operations
    before_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# System Configuration
# ---------------------------------------------------------------------------


class SystemConfig(Base):
    __tablename__ = "system_configs"
    __table_args__ = (
        Index("ix_identity_config_key", "key"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="string"
    )  # string, int, bool, json
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Feature Flags
# ---------------------------------------------------------------------------


class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    __table_args__ = (
        Index("ix_identity_ff_key", "key"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="OFF"
    )  # ON, OFF, PARTIAL
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_institutions: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=list
    )
    auto_enable_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_identity_incident_status", "status"),
        Index("ix_identity_incident_severity", "severity"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)  # SEV1-4
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="OPEN"
    )
    affected_services: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=list
    )
    affected_institutions: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=list
    )
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    postmortem_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timeline: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------


class Announcement(Base):
    __tablename__ = "announcements"
    __table_args__ = (
        Index("ix_identity_announcement_status", "is_active"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    announcement_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="INFO"
    )  # INFO, WARNING, CRITICAL, PROMO, SUCCESS
    position: Mapped[str] = mapped_column(
        String(20), nullable=False, default="TOP_BANNER"
    )
    target_audience: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_dismissable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_once: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_ack: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Approval Workflow
# ---------------------------------------------------------------------------


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    __table_args__ = (
        Index("ix_identity_approval_status", "status"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    priority: Mapped[str] = mapped_column(
        String(10), nullable=False, default="MEDIUM"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    requested_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Scheduled Maintenance
# ---------------------------------------------------------------------------


class ScheduledMaintenance(Base):
    __tablename__ = "scheduled_maintenances"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    scheduled_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SCHEDULED"
    )
    affected_services: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=list
    )
    auto_notify: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Subscription Plan Definition
# ---------------------------------------------------------------------------


class PlanDefinition(Base):
    __tablename__ = "plan_definitions"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Pricing
    price_monthly: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    price_quarterly: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    price_annual: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Limits
    max_students: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_teachers: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    api_rate_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Features included
    features: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # Display
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Impersonation Log
# ---------------------------------------------------------------------------


class ImpersonationLog(Base):
    __tablename__ = "impersonation_logs"
    __table_args__ = (
        Index("ix_identity_impersonation_admin", "admin_user_id"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    admin_user_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    target_user_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actions_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# IP Block List
# ---------------------------------------------------------------------------


class IPBlock(Base):
    __tablename__ = "ip_blocks"
    __table_args__ = (
        Index("ix_identity_ip_block_ip", "ip_address"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    ip_range: Mapped[str | None] = mapped_column(String(45), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocked_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Configuration History (for rollback)
# ---------------------------------------------------------------------------


class ConfigHistory(Base):
    __tablename__ = "config_history"
    __table_args__ = (
        Index("ix_identity_config_hist_key", "config_key"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    config_key: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    changed_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
