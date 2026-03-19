"""User, UserRoleAssignment, and Session models."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_identity_users_phone", "phone"),
        Index("ix_identity_users_email", "email"),
        Index("ix_identity_users_institution_id", "institution_id"),
        Index("ix_identity_users_status", "status"),
        Index("ix_identity_users_primary_role", "primary_role"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Primary role (for quick lookups — the "main" role)
    primary_role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="STUDENT"
    )

    # Institution binding (nullable for platform-level staff)
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.institutions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, schema="identity"),
        nullable=False,
        default=UserStatus.ACTIVE,
    )

    # Platform staff fields
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reporting_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    assigned_boards: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=list
    )
    assigned_subjects: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=list
    )

    # Metadata
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    login_count: Mapped[int] = mapped_column(default=0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    # Relationships
    institution = relationship("Institution", back_populates="users", lazy="selectin")
    sessions = relationship("Session", back_populates="user", lazy="selectin")
    role_assignments = relationship(
        "UserRoleAssignment", back_populates="user", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Role Assignment (many-to-many: user can have multiple roles, scoped)
# ---------------------------------------------------------------------------


class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"
    __table_args__ = (
        Index("ix_identity_ura_user", "user_id"),
        Index("ix_identity_ura_role", "role"),
        Index("ix_identity_ura_scope", "scope_type", "scope_id"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    # Scope: where this role applies
    scope_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="platform"
    )  # platform, group, institution
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # group_id or institution_id

    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="role_assignments")
