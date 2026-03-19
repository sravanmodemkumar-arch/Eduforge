"""Institution, InstitutionGroup, and Domain models."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InstitutionType(str, enum.Enum):
    SCHOOL = "SCHOOL"
    COLLEGE = "COLLEGE"
    COACHING = "COACHING"
    GROUP = "GROUP"
    MOCK_TEST_DOMAIN = "MOCK_TEST_DOMAIN"
    UNIVERSITY = "UNIVERSITY"


class InstitutionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    TRIAL = "TRIAL"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    PENDING_SETUP = "PENDING_SETUP"
    DELETED = "DELETED"


class SubscriptionPlan(str, enum.Enum):
    FREE_TRIAL = "FREE_TRIAL"
    STARTER = "STARTER"
    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"
    GROUP = "GROUP"
    MOCK_TEST_SITE = "MOCK_TEST_SITE"
    CUSTOM = "CUSTOM"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    TRIAL = "TRIAL"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    PENDING_SETUP = "PENDING_SETUP"


# ---------------------------------------------------------------------------
# Institution Group (University / College Chain)
# ---------------------------------------------------------------------------


class InstitutionGroup(Base):
    __tablename__ = "institution_groups"
    __table_args__ = (
        Index("ix_identity_groups_name", "name"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    group_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UNIVERSITY"
    )
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Subscription
    subscription_plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subscription_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    subscription_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

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
    institutions = relationship(
        "Institution", back_populates="group", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Institution (College / School / Coaching / Mock Test Domain)
# ---------------------------------------------------------------------------


class Institution(Base):
    __tablename__ = "institutions"
    __table_args__ = (
        Index("ix_identity_inst_type", "institution_type"),
        Index("ix_identity_inst_status", "status"),
        Index("ix_identity_inst_group", "group_id"),
        Index("ix_identity_inst_state", "state"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    institution_type: Mapped[InstitutionType] = mapped_column(
        Enum(InstitutionType, schema="identity"), nullable=False
    )
    status: Mapped[InstitutionStatus] = mapped_column(
        Enum(InstitutionStatus, schema="identity"),
        nullable=False,
        default=InstitutionStatus.PENDING_SETUP,
    )

    # Group (optional — for colleges in a university/chain)
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.institution_groups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Contact
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Address
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Branding / White-label
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    secondary_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    custom_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    login_template: Mapped[str | None] = mapped_column(String(50), nullable=True)
    welcome_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Subscription
    subscription_plan: Mapped[SubscriptionPlan | None] = mapped_column(
        Enum(SubscriptionPlan, schema="identity"), nullable=True
    )
    subscription_status: Mapped[SubscriptionStatus | None] = mapped_column(
        Enum(SubscriptionStatus, schema="identity"), nullable=True
    )
    subscription_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    subscription_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    subscription_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    billing_cycle: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Limits
    max_students: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    api_rate_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Features (JSONB for flexible feature flags per institution)
    features_enabled: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=dict
    )

    # Board / Affiliation
    board_affiliations: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=list
    )

    # Health & Engagement
    health_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_admin_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Onboarding
    onboarding_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    onboarding_specialist_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    go_live_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Sales
    sales_executive_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    account_manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Metadata
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)
    internal_notes: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, default=list
    )

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
    group = relationship("InstitutionGroup", back_populates="institutions", lazy="selectin")
    users = relationship("User", back_populates="institution", lazy="selectin")
    domains = relationship("Domain", back_populates="institution", lazy="selectin")


# ---------------------------------------------------------------------------
# Domain (Mock test sites + institution custom domains)
# ---------------------------------------------------------------------------


class Domain(Base):
    __tablename__ = "domains"
    __table_args__ = (
        Index("ix_identity_domain_name", "domain_name"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    domain_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SUBDOMAIN"
    )  # SUBDOMAIN, CNAME, CUSTOM
    ssl_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ssl_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dns_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cdn_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # For mock test domains
    exam_focus: Mapped[str | None] = mapped_column(String(255), nullable=True)
    landing_template: Mapped[str | None] = mapped_column(String(50), nullable=True)
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_analytics_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ad_integration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    social_links: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    institution = relationship("Institution", back_populates="domains", lazy="selectin")
