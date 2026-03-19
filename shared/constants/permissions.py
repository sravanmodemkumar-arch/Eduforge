"""Granular permission definitions for EduForge RBAC system."""

from enum import StrEnum

from shared.constants.roles import PlatformRole


class Permission(StrEnum):
    """Fine-grained permissions mapped to roles."""

    # ── Institution Management ────────────────────────────────────────────
    INSTITUTION_VIEW = "institution:view"
    INSTITUTION_CREATE = "institution:create"
    INSTITUTION_EDIT = "institution:edit"
    INSTITUTION_DELETE = "institution:delete"
    INSTITUTION_SUSPEND = "institution:suspend"
    INSTITUTION_TRANSFER = "institution:transfer"
    INSTITUTION_MERGE = "institution:merge"
    INSTITUTION_IMPERSONATE = "institution:impersonate"

    # ── Group Management ──────────────────────────────────────────────────
    GROUP_VIEW = "group:view"
    GROUP_CREATE = "group:create"
    GROUP_EDIT = "group:edit"
    GROUP_DELETE = "group:delete"

    # ── User Management ───────────────────────────────────────────────────
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"
    USER_BLOCK = "user:block"
    USER_IMPERSONATE = "user:impersonate"
    USER_BULK_IMPORT = "user:bulk_import"
    USER_BULK_DELETE = "user:bulk_delete"
    USER_TRANSFER = "user:transfer"
    USER_ROLE_ASSIGN = "user:role_assign"

    # ── Subscription & Billing ────────────────────────────────────────────
    SUBSCRIPTION_VIEW = "subscription:view"
    SUBSCRIPTION_CREATE = "subscription:create"
    SUBSCRIPTION_EDIT = "subscription:edit"
    SUBSCRIPTION_CANCEL = "subscription:cancel"
    PLAN_VIEW = "plan:view"
    PLAN_CREATE = "plan:create"
    PLAN_EDIT = "plan:edit"
    PLAN_DELETE = "plan:delete"
    REVENUE_VIEW = "revenue:view"
    PAYMENT_VIEW = "payment:view"
    PAYMENT_REFUND = "payment:refund"
    DISCOUNT_APPROVE = "discount:approve"

    # ── Domain Management ─────────────────────────────────────────────────
    DOMAIN_VIEW = "domain:view"
    DOMAIN_CREATE = "domain:create"
    DOMAIN_EDIT = "domain:edit"
    DOMAIN_DELETE = "domain:delete"

    # ── System Configuration ──────────────────────────────────────────────
    CONFIG_VIEW = "config:view"
    CONFIG_EDIT = "config:edit"
    FEATURE_FLAG_VIEW = "feature_flag:view"
    FEATURE_FLAG_EDIT = "feature_flag:edit"
    EXTERNAL_SERVICE_VIEW = "external_service:view"
    EXTERNAL_SERVICE_EDIT = "external_service:edit"
    TEMPLATE_VIEW = "template:view"
    TEMPLATE_EDIT = "template:edit"

    # ── Security ──────────────────────────────────────────────────────────
    AUDIT_LOG_VIEW = "audit_log:view"
    LOGIN_MONITOR_VIEW = "login_monitor:view"
    IP_BLOCK_VIEW = "ip_block:view"
    IP_BLOCK_EDIT = "ip_block:edit"
    DATA_ACCESS_LOG_VIEW = "data_access_log:view"
    SESSION_VIEW = "session:view"
    SESSION_TERMINATE = "session:terminate"

    # ── Infrastructure ────────────────────────────────────────────────────
    INFRA_VIEW = "infra:view"
    INFRA_MANAGE = "infra:manage"
    SERVICE_RESTART = "service:restart"
    CACHE_FLUSH = "cache:flush"
    DB_CONSOLE = "db:console"
    BACKUP_VIEW = "backup:view"
    BACKUP_MANAGE = "backup:manage"
    BACKUP_RESTORE = "backup:restore"

    # ── Content ───────────────────────────────────────────────────────────
    CONTENT_VIEW = "content:view"
    CONTENT_CREATE = "content:create"
    CONTENT_EDIT = "content:edit"
    CONTENT_DELETE = "content:delete"
    CONTENT_APPROVE = "content:approve"
    CONTENT_FLAG = "content:flag"
    CONTENT_MODERATE = "content:moderate"

    # ── Compliance ────────────────────────────────────────────────────────
    COMPLIANCE_VIEW = "compliance:view"
    COMPLIANCE_MANAGE = "compliance:manage"
    DATA_REQUEST_VIEW = "data_request:view"
    DATA_REQUEST_PROCESS = "data_request:process"

    # ── Emergency ─────────────────────────────────────────────────────────
    EMERGENCY_MAINTENANCE = "emergency:maintenance"
    EMERGENCY_STOP_EXAMS = "emergency:stop_exams"
    EMERGENCY_FREEZE_INSTITUTION = "emergency:freeze_institution"
    EMERGENCY_REVOKE_SESSIONS = "emergency:revoke_sessions"
    EMERGENCY_ROTATE_SECRETS = "emergency:rotate_secrets"

    # ── Analytics ─────────────────────────────────────────────────────────
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    REPORT_GENERATE = "report:generate"
    LEADERBOARD_MANAGE = "leaderboard:manage"

    # ── Communication ─────────────────────────────────────────────────────
    NOTIFICATION_VIEW = "notification:view"
    NOTIFICATION_SEND = "notification:send"
    BROADCAST_SEND = "broadcast:send"
    ANNOUNCEMENT_CREATE = "announcement:create"
    ANNOUNCEMENT_EDIT = "announcement:edit"

    # ── Approval Workflow ─────────────────────────────────────────────────
    APPROVAL_VIEW = "approval:view"
    APPROVAL_APPROVE = "approval:approve"
    APPROVAL_REJECT = "approval:reject"

    # ── Export & Data Operations ──────────────────────────────────────────
    EXPORT_VIEW = "export:view"
    EXPORT_CREATE = "export:create"
    EXPORT_PII = "export:pii"
    TRASH_VIEW = "trash:view"
    TRASH_RESTORE = "trash:restore"
    TRASH_PURGE = "trash:purge"
    ARCHIVAL_MANAGE = "archival:manage"

    # ── Incidents & War Room ──────────────────────────────────────────────
    INCIDENT_VIEW = "incident:view"
    INCIDENT_CREATE = "incident:create"
    INCIDENT_MANAGE = "incident:manage"
    WAR_ROOM_ACCESS = "war_room:access"

    # ── Mobile App ────────────────────────────────────────────────────────
    MOBILE_APP_VIEW = "mobile_app:view"
    MOBILE_APP_MANAGE = "mobile_app:manage"

    # ── Cost Center ───────────────────────────────────────────────────────
    COST_VIEW = "cost:view"
    COST_MANAGE = "cost:manage"

    # ── Onboarding ────────────────────────────────────────────────────────
    ONBOARDING_VIEW = "onboarding:view"
    ONBOARDING_MANAGE = "onboarding:manage"

    # ── Developer Tools ───────────────────────────────────────────────────
    API_PLAYGROUND = "api:playground"
    WEBHOOK_DEBUG = "webhook:debug"
    CHANGELOG_VIEW = "changelog:view"
    CHANGELOG_EDIT = "changelog:edit"
    DOCS_VIEW = "docs:view"
    DOCS_EDIT = "docs:edit"

    # ── Vendor & Payment Gateway ──────────────────────────────────────────
    VENDOR_HEALTH_VIEW = "vendor_health:view"
    PAYMENT_GATEWAY_VIEW = "payment_gateway:view"
    PAYMENT_GATEWAY_MANAGE = "payment_gateway:manage"

    # ── White Label & Branding ────────────────────────────────────────────
    WHITELABEL_VIEW = "whitelabel:view"
    WHITELABEL_PREVIEW = "whitelabel:preview"
    WHITELABEL_EDIT = "whitelabel:edit"

    # ── Capacity & Load ───────────────────────────────────────────────────
    CAPACITY_VIEW = "capacity:view"
    CAPACITY_MANAGE = "capacity:manage"

    # ── Search & Indexing ─────────────────────────────────────────────────
    SEARCH_INDEX_VIEW = "search_index:view"
    SEARCH_INDEX_MANAGE = "search_index:manage"

    # ── License & Certificates ────────────────────────────────────────────
    LICENSE_VIEW = "license:view"
    LICENSE_GENERATE = "license:generate"

    # ── Config History ────────────────────────────────────────────────────
    CONFIG_HISTORY_VIEW = "config_history:view"
    CONFIG_ROLLBACK = "config:rollback"

    # ── Tenant Isolation ──────────────────────────────────────────────────
    TENANT_AUDIT_VIEW = "tenant_audit:view"
    TENANT_AUDIT_RUN = "tenant_audit:run"

    # ── Maintenance ───────────────────────────────────────────────────────
    MAINTENANCE_VIEW = "maintenance:view"
    MAINTENANCE_SCHEDULE = "maintenance:schedule"

    # ── Storage & Media ───────────────────────────────────────────────────
    STORAGE_VIEW = "storage:view"
    STORAGE_MANAGE = "storage:manage"
    CDN_PURGE = "cdn:purge"

    # ── Error Tracking ────────────────────────────────────────────────────
    ERROR_VIEW = "error:view"
    ERROR_MANAGE = "error:manage"

    # ── Deliverability ────────────────────────────────────────────────────
    DELIVERABILITY_VIEW = "deliverability:view"
    DELIVERABILITY_MANAGE = "deliverability:manage"

    # ── Revenue Forecasting ───────────────────────────────────────────────
    FORECAST_VIEW = "forecast:view"

    # ── Platform Health Score ─────────────────────────────────────────────
    HEALTH_SCORE_VIEW = "health_score:view"


# ---------------------------------------------------------------------------
# Role → Permissions Mapping
# ---------------------------------------------------------------------------

# Helper: all permissions
_ALL_PERMISSIONS = [p.value for p in Permission]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    # ── SUPER_ADMIN — everything ──────────────────────────────────────────
    PlatformRole.SUPER_ADMIN: _ALL_PERMISSIONS,

    # ── PLATFORM_ADMIN — business operations, no infra/emergency ──────────
    PlatformRole.PLATFORM_ADMIN: [
        # Institution
        Permission.INSTITUTION_VIEW, Permission.INSTITUTION_CREATE,
        Permission.INSTITUTION_EDIT, Permission.INSTITUTION_SUSPEND,
        Permission.INSTITUTION_IMPERSONATE,
        # Group
        Permission.GROUP_VIEW, Permission.GROUP_CREATE, Permission.GROUP_EDIT,
        # User
        Permission.USER_VIEW, Permission.USER_CREATE, Permission.USER_EDIT,
        Permission.USER_BLOCK, Permission.USER_IMPERSONATE,
        Permission.USER_BULK_IMPORT, Permission.USER_TRANSFER,
        Permission.USER_ROLE_ASSIGN,
        # Subscription
        Permission.SUBSCRIPTION_VIEW, Permission.SUBSCRIPTION_CREATE,
        Permission.SUBSCRIPTION_EDIT,
        Permission.PLAN_VIEW, Permission.REVENUE_VIEW,
        Permission.PAYMENT_VIEW, Permission.DISCOUNT_APPROVE,
        # Domain
        Permission.DOMAIN_VIEW, Permission.DOMAIN_EDIT,
        # Config (view only)
        Permission.CONFIG_VIEW, Permission.FEATURE_FLAG_VIEW,
        Permission.EXTERNAL_SERVICE_VIEW,
        Permission.TEMPLATE_VIEW, Permission.TEMPLATE_EDIT,
        # Security (view only)
        Permission.AUDIT_LOG_VIEW, Permission.LOGIN_MONITOR_VIEW,
        Permission.SESSION_VIEW,
        # Content
        Permission.CONTENT_VIEW, Permission.CONTENT_FLAG,
        Permission.CONTENT_MODERATE,
        # Compliance
        Permission.COMPLIANCE_VIEW, Permission.DATA_REQUEST_VIEW,
        Permission.DATA_REQUEST_PROCESS,
        # Analytics
        Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT,
        Permission.REPORT_GENERATE,
        # Communication
        Permission.NOTIFICATION_VIEW, Permission.NOTIFICATION_SEND,
        Permission.BROADCAST_SEND,
        Permission.ANNOUNCEMENT_CREATE, Permission.ANNOUNCEMENT_EDIT,
        # Approval
        Permission.APPROVAL_VIEW, Permission.APPROVAL_APPROVE,
        Permission.APPROVAL_REJECT,
        # Export
        Permission.EXPORT_VIEW, Permission.EXPORT_CREATE,
        # Onboarding
        Permission.ONBOARDING_VIEW, Permission.ONBOARDING_MANAGE,
        # Health & Forecast
        Permission.HEALTH_SCORE_VIEW, Permission.FORECAST_VIEW,
        # Vendor
        Permission.VENDOR_HEALTH_VIEW,
        # Notes & Tags (implicit from institution views)
    ],

    # ── OPERATIONS_MANAGER — daily ops, content, support oversight ────────
    PlatformRole.OPERATIONS_MANAGER: [
        # Institution (read)
        Permission.INSTITUTION_VIEW,
        # User (read)
        Permission.USER_VIEW,
        # Content (full)
        Permission.CONTENT_VIEW, Permission.CONTENT_FLAG,
        Permission.CONTENT_MODERATE, Permission.CONTENT_DELETE,
        # Compliance
        Permission.COMPLIANCE_VIEW, Permission.COMPLIANCE_MANAGE,
        Permission.DATA_REQUEST_VIEW, Permission.DATA_REQUEST_PROCESS,
        # Analytics (read)
        Permission.ANALYTICS_VIEW, Permission.REPORT_GENERATE,
        # Communication
        Permission.NOTIFICATION_VIEW, Permission.NOTIFICATION_SEND,
        Permission.BROADCAST_SEND,
        Permission.ANNOUNCEMENT_CREATE, Permission.ANNOUNCEMENT_EDIT,
        # Approval (limited)
        Permission.APPROVAL_VIEW,
        # Export (own)
        Permission.EXPORT_VIEW, Permission.EXPORT_CREATE,
        # Health
        Permission.HEALTH_SCORE_VIEW,
        # Onboarding (read)
        Permission.ONBOARDING_VIEW,
        # Deliverability
        Permission.DELIVERABILITY_VIEW,
    ],
}
