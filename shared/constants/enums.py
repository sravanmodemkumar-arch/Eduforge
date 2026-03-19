"""Platform-wide enumerations for EduForge."""

from enum import StrEnum


class InstitutionType(StrEnum):
    SCHOOL = "SCHOOL"
    COLLEGE = "COLLEGE"
    COACHING = "COACHING"
    GROUP = "GROUP"
    MOCK_TEST_DOMAIN = "MOCK_TEST_DOMAIN"
    UNIVERSITY = "UNIVERSITY"


class SubscriptionPlan(StrEnum):
    FREE_TRIAL = "FREE_TRIAL"
    STARTER = "STARTER"
    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"
    GROUP = "GROUP"
    MOCK_TEST_SITE = "MOCK_TEST_SITE"
    CUSTOM = "CUSTOM"


class SubscriptionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    TRIAL = "TRIAL"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    PENDING_SETUP = "PENDING_SETUP"


class InstitutionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    TRIAL = "TRIAL"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    PENDING_SETUP = "PENDING_SETUP"
    DELETED = "DELETED"


class ContentStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    FLAGGED = "FLAGGED"
    ARCHIVED = "ARCHIVED"


class ContentType(StrEnum):
    MCQ = "MCQ"
    NOTE = "NOTE"
    VIDEO = "VIDEO"
    TEST = "TEST"
    PYP = "PYP"
    CURRENT_AFFAIRS = "CURRENT_AFFAIRS"
    STUDY_MATERIAL = "STUDY_MATERIAL"


class FeatureFlagStatus(StrEnum):
    ON = "ON"
    OFF = "OFF"
    PARTIAL = "PARTIAL"


class IncidentSeverity(StrEnum):
    SEV1 = "SEV1"  # Critical — platform down
    SEV2 = "SEV2"  # Major — feature broken
    SEV3 = "SEV3"  # Minor — degraded performance
    SEV4 = "SEV4"  # Low — cosmetic issue


class IncidentStatus(StrEnum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    IDENTIFIED = "IDENTIFIED"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"
    POSTMORTEM = "POSTMORTEM"


class AlertSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class AuditAction(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    IMPERSONATE = "IMPERSONATE"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SUSPEND = "SUSPEND"
    RESTORE = "RESTORE"
    PURGE = "PURGE"
    EMERGENCY = "EMERGENCY"
    BULK_OPERATION = "BULK_OPERATION"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


class OnboardingStage(StrEnum):
    SIGNED_UP = "SIGNED_UP"
    DATA_IMPORT = "DATA_IMPORT"
    TRAINING = "TRAINING"
    GO_LIVE = "GO_LIVE"
    COMPLETED = "COMPLETED"


class ServiceStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    MAINTENANCE = "MAINTENANCE"


class MaintenanceStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AnnouncementType(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    PROMO = "PROMO"
    SUCCESS = "SUCCESS"


class AnnouncementPosition(StrEnum):
    TOP_BANNER = "TOP_BANNER"
    BOTTOM_BANNER = "BOTTOM_BANNER"
    MODAL_POPUP = "MODAL_POPUP"
    SIDEBAR = "SIDEBAR"
