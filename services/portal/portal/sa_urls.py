"""URL configuration for Super Admin pages — all 54 pages."""

from django.urls import path

from portal.views.superadmin.dashboard import (
    sa_dashboard,
    sa_dashboard_alerts,
    sa_dashboard_activity,
    sa_dashboard_stats,
)
from portal.views.superadmin.institutions import (
    institution_create,
    institution_detail,
    institution_groups,
    institution_list,
)
from portal.views.superadmin.users import (
    impersonation_log,
    platform_staff,
    user_detail,
    user_list,
)
from portal.views.superadmin.pages import (
    activity_stream,
    alerts_config,
    announcements,
    api_playground,
    approval_queue,
    archival_policy,
    audit_forensics,
    backup_dr,
    bulk_operations,
    calendar_view,
    certificates,
    changelog,
    compliance_data_requests,
    compliance_reports,
    compliance_tenant_audit,
    config_external_services,
    config_feature_flags,
    config_global,
    config_history,
    config_templates,
    content_flagged,
    content_overview,
    content_productivity,
    cost_center,
    db_console,
    deliverability,
    developer_docs,
    domain_custom,
    domain_mock_sites,
    emergency_controls,
    error_tracking,
    export_center,
    health_score,
    incident_list,
    infra_cache,
    infra_database,
    infra_jobs,
    infra_services,
    inst_transfer_merge,
    load_capacity,
    maintenance_planner,
    map_view,
    mobile_app,
    onboarding_tracker,
    payment_gateway,
    search_indexing,
    security_audit_log,
    security_data_access,
    security_ip_blocks,
    security_login_monitor,
    security_sessions,
    storage_media,
    subscription_forecast,
    subscription_list,
    subscription_plans,
    subscription_revenue,
    trash_bin,
    vendor_health,
    war_room,
    whitelabel_preview,
)

app_name = "sa"

urlpatterns = [
    # ── 1. Command Center Dashboard ──────────────────────────────────────
    path("", sa_dashboard, name="dashboard"),
    path("dashboard/stats/", sa_dashboard_stats, name="dashboard-stats"),
    path("dashboard/alerts/", sa_dashboard_alerts, name="dashboard-alerts"),
    path("dashboard/activity/", sa_dashboard_activity, name="dashboard-activity"),

    # ── 2. Institution Management ─────────────────────────────────────────
    path("institutions/", institution_list, name="institution-list"),
    path("institutions/create/", institution_create, name="institution-create"),
    path("institutions/groups/", institution_groups, name="institution-groups"),
    path("institutions/transfer-merge/", inst_transfer_merge, name="institution-transfer"),
    path("institutions/<uuid:institution_id>/", institution_detail, name="institution-detail"),

    # ── 3. User Management ────────────────────────────────────────────────
    path("users/", user_list, name="user-list"),
    path("users/platform-staff/", platform_staff, name="platform-staff"),
    path("users/impersonation-log/", impersonation_log, name="impersonation-log"),
    path("users/<uuid:user_id>/", user_detail, name="user-detail"),

    # ── 4. Domain Management ──────────────────────────────────────────────
    path("domains/mock-sites/", domain_mock_sites, name="domain-mock-sites"),
    path("domains/custom/", domain_custom, name="domain-custom"),

    # ── 5. Subscription & Billing ─────────────────────────────────────────
    path("subscriptions/plans/", subscription_plans, name="subscription-plans"),
    path("subscriptions/", subscription_list, name="subscription-list"),
    path("subscriptions/revenue/", subscription_revenue, name="subscription-revenue"),
    path("subscriptions/forecast/", subscription_forecast, name="subscription-forecast"),

    # ── 6. System Configuration ───────────────────────────────────────────
    path("config/", config_global, name="config-global"),
    path("config/feature-flags/", config_feature_flags, name="config-feature-flags"),
    path("config/external-services/", config_external_services, name="config-external-services"),
    path("config/templates/", config_templates, name="config-templates"),
    path("config/history/", config_history, name="config-history"),

    # ── 7. Security ───────────────────────────────────────────────────────
    path("security/audit-log/", security_audit_log, name="security-audit-log"),
    path("security/login-monitor/", security_login_monitor, name="security-login-monitor"),
    path("security/ip-blocks/", security_ip_blocks, name="security-ip-blocks"),
    path("security/sessions/", security_sessions, name="security-sessions"),
    path("security/data-access/", security_data_access, name="security-data-access"),

    # ── 8. Infrastructure ─────────────────────────────────────────────────
    path("infra/services/", infra_services, name="infra-services"),
    path("infra/database/", infra_database, name="infra-database"),
    path("infra/jobs/", infra_jobs, name="infra-jobs"),
    path("infra/cache/", infra_cache, name="infra-cache"),

    # ── 9. Content Oversight ──────────────────────────────────────────────
    path("content/", content_overview, name="content-overview"),
    path("content/flagged/", content_flagged, name="content-flagged"),
    path("content/productivity/", content_productivity, name="content-productivity"),

    # ── 10. Compliance ────────────────────────────────────────────────────
    path("compliance/data-requests/", compliance_data_requests, name="compliance-data-requests"),
    path("compliance/reports/", compliance_reports, name="compliance-reports"),
    path("compliance/tenant-audit/", compliance_tenant_audit, name="compliance-tenant-audit"),

    # ── 11. Emergency Controls ────────────────────────────────────────────
    path("emergency/", emergency_controls, name="emergency-controls"),

    # ── 14. Activity Stream ───────────────────────────────────────────────
    path("activity/", activity_stream, name="activity-stream"),

    # ── 15. Map View ──────────────────────────────────────────────────────
    path("map/", map_view, name="map-view"),

    # ── 16. Calendar ──────────────────────────────────────────────────────
    path("calendar/", calendar_view, name="calendar"),

    # ── 17. Trash ─────────────────────────────────────────────────────────
    path("trash/", trash_bin, name="trash"),

    # ── 18. Export Center ─────────────────────────────────────────────────
    path("exports/", export_center, name="export-center"),

    # ── 21. Onboarding ────────────────────────────────────────────────────
    path("onboarding/", onboarding_tracker, name="onboarding"),

    # ── 23. Approvals ─────────────────────────────────────────────────────
    path("approvals/", approval_queue, name="approvals"),

    # ── 24. Announcements ─────────────────────────────────────────────────
    path("announcements/", announcements, name="announcements"),

    # ── 25. API Playground ────────────────────────────────────────────────
    path("api-playground/", api_playground, name="api-playground"),

    # ── 26. Database Console ──────────────────────────────────────────────
    path("db-console/", db_console, name="db-console"),

    # ── 29. Backup & DR ───────────────────────────────────────────────────
    path("backup/", backup_dr, name="backup"),

    # ── 30. Incidents ─────────────────────────────────────────────────────
    path("incidents/", incident_list, name="incidents"),

    # ── 31. Cost Center ───────────────────────────────────────────────────
    path("cost-center/", cost_center, name="cost-center"),

    # ── 32. Storage ───────────────────────────────────────────────────────
    path("storage/", storage_media, name="storage"),

    # ── 33. Mobile App ────────────────────────────────────────────────────
    path("mobile-app/", mobile_app, name="mobile-app"),

    # ── 35. Error Tracking ────────────────────────────────────────────────
    path("errors/", error_tracking, name="errors"),

    # ── 36. Deliverability ────────────────────────────────────────────────
    path("deliverability/", deliverability, name="deliverability"),

    # ── 37. Config History ────────────────────────────────────────────────
    # (already under /config/history/)

    # ── 38. Maintenance ───────────────────────────────────────────────────
    path("maintenance/", maintenance_planner, name="maintenance"),

    # ── 40. Search & Indexing ─────────────────────────────────────────────
    path("search-indexing/", search_indexing, name="search-indexing"),

    # ── 41. Load & Capacity ───────────────────────────────────────────────
    path("load-capacity/", load_capacity, name="load-capacity"),

    # ── 42. Changelog ─────────────────────────────────────────────────────
    path("changelog/", changelog, name="changelog"),

    # ── 43. Developer Docs ────────────────────────────────────────────────
    path("docs/", developer_docs, name="docs"),

    # ── 44. Payment Gateway ───────────────────────────────────────────────
    path("payment-gateway/", payment_gateway, name="payment-gateway"),

    # ── 45. Transfer & Merge ──────────────────────────────────────────────
    # (already under /institutions/transfer-merge/)

    # ── 46. Bulk Operations ───────────────────────────────────────────────
    path("bulk-ops/", bulk_operations, name="bulk-ops"),

    # ── 47. Alerts Config ─────────────────────────────────────────────────
    path("alerts-config/", alerts_config, name="alerts-config"),

    # ── 48. Audit Forensics ───────────────────────────────────────────────
    path("forensics/", audit_forensics, name="forensics"),

    # ── 49. Archival Policy ───────────────────────────────────────────────
    path("archival/", archival_policy, name="archival"),

    # ── 50. Vendor Health ─────────────────────────────────────────────────
    path("vendor-health/", vendor_health, name="vendor-health"),

    # ── 51. White-Label Preview ───────────────────────────────────────────
    path("whitelabel-preview/", whitelabel_preview, name="whitelabel-preview"),

    # ── 52. War Room ──────────────────────────────────────────────────────
    path("war-room/", war_room, name="war-room"),

    # ── 53. Health Score ──────────────────────────────────────────────────
    path("health-score/", health_score, name="health-score"),

    # ── 54. Certificates ──────────────────────────────────────────────────
    path("certificates/", certificates, name="certificates"),
]
