"""All EduForge roles — Platform (50), Group (8), Institution (18), End-User (3)."""

from enum import StrEnum


# ---------------------------------------------------------------------------
# Platform-Level Roles (50) — EduForge internal employees
# ---------------------------------------------------------------------------


class PlatformRole(StrEnum):
    """Roles for platform-level staff (EduForge employees)."""

    # 1. Super Administration (3)
    SUPER_ADMIN = "SUPER_ADMIN"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    OPERATIONS_MANAGER = "OPERATIONS_MANAGER"

    # 2. Engineering & Infrastructure (3)
    INFRA_ADMIN = "INFRA_ADMIN"
    API_MANAGER = "API_MANAGER"
    SECURITY_ADMIN = "SECURITY_ADMIN"

    # 3. Product & Catalog (3)
    PRODUCT_MANAGER = "PRODUCT_MANAGER"
    CATALOG_MANAGER = "CATALOG_MANAGER"
    WHITE_LABEL_MANAGER = "WHITE_LABEL_MANAGER"

    # 4. Sales & Business Development (5)
    SALES_MANAGER = "SALES_MANAGER"
    SALES_EXECUTIVE = "SALES_EXECUTIVE"
    ACCOUNT_MANAGER = "ACCOUNT_MANAGER"
    PARTNERSHIP_MANAGER = "PARTNERSHIP_MANAGER"
    MARKETING_MANAGER = "MARKETING_MANAGER"

    # 5. Customer Operations (4)
    SUPPORT_MANAGER = "SUPPORT_MANAGER"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    ONBOARDING_SPECIALIST = "ONBOARDING_SPECIALIST"
    CUSTOMER_SUCCESS_MANAGER = "CUSTOMER_SUCCESS_MANAGER"

    # 6. Curriculum & Board Management (3)
    CURRICULUM_MANAGER = "CURRICULUM_MANAGER"
    EXAM_PATTERN_MANAGER = "EXAM_PATTERN_MANAGER"
    SUBJECT_MATTER_EXPERT = "SUBJECT_MATTER_EXPERT"

    # 7. MCQ / Question Bank (4)
    QUESTION_CREATOR = "QUESTION_CREATOR"
    QUESTION_REVIEWER = "QUESTION_REVIEWER"
    QUESTION_BANK_MANAGER = "QUESTION_BANK_MANAGER"
    QUESTION_IMPORTER = "QUESTION_IMPORTER"

    # 8. Notes & Study Material (4)
    NOTES_CREATOR = "NOTES_CREATOR"
    NOTES_REVIEWER = "NOTES_REVIEWER"
    STUDY_MATERIAL_MANAGER = "STUDY_MATERIAL_MANAGER"
    PREVIOUS_YEAR_PAPER_MANAGER = "PREVIOUS_YEAR_PAPER_MANAGER"

    # 9. Video Content (3)
    VIDEO_CREATOR = "VIDEO_CREATOR"
    VIDEO_REVIEWER = "VIDEO_REVIEWER"
    VIDEO_PLAYLIST_MANAGER = "VIDEO_PLAYLIST_MANAGER"

    # 10. Test & Assessment (4)
    TEST_CREATOR = "TEST_CREATOR"
    TEST_REVIEWER = "TEST_REVIEWER"
    TEST_SCHEDULER = "TEST_SCHEDULER"
    TEST_ANALYTICS_MANAGER = "TEST_ANALYTICS_MANAGER"

    # 11. Current Affairs & Daily Content (2)
    CURRENT_AFFAIRS_EDITOR = "CURRENT_AFFAIRS_EDITOR"
    EDITORIAL_MANAGER = "EDITORIAL_MANAGER"

    # 12. Finance & Subscription (3)
    FINANCE_ADMIN = "FINANCE_ADMIN"
    SUBSCRIPTION_MANAGER = "SUBSCRIPTION_MANAGER"
    PAYOUT_MANAGER = "PAYOUT_MANAGER"

    # 13. Analytics & Reporting (3)
    DATA_ANALYST = "DATA_ANALYST"
    REPORT_TEMPLATE_MANAGER = "REPORT_TEMPLATE_MANAGER"
    LEADERBOARD_MANAGER = "LEADERBOARD_MANAGER"

    # 14. Communication & Notifications (3)
    NOTIFICATION_ADMIN = "NOTIFICATION_ADMIN"
    BROADCAST_MANAGER = "BROADCAST_MANAGER"
    COMMUNITY_MODERATOR = "COMMUNITY_MODERATOR"

    # 15. Compliance & Legal (2)
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    ABUSE_PREVENTION_MANAGER = "ABUSE_PREVENTION_MANAGER"

    # 16. Data Operations (2)
    DATA_OPERATIONS_MANAGER = "DATA_OPERATIONS_MANAGER"
    CONTENT_MIGRATION_SPECIALIST = "CONTENT_MIGRATION_SPECIALIST"


# ---------------------------------------------------------------------------
# Group-Level Roles (8)
# ---------------------------------------------------------------------------


class GroupRole(StrEnum):
    """Roles for college-group / university / coaching-chain level."""

    GROUP_OWNER = "GROUP_OWNER"
    GROUP_ADMIN = "GROUP_ADMIN"
    GROUP_ACADEMIC_HEAD = "GROUP_ACADEMIC_HEAD"
    GROUP_CONTENT_MANAGER = "GROUP_CONTENT_MANAGER"
    GROUP_EXAM_CONTROLLER = "GROUP_EXAM_CONTROLLER"
    GROUP_FINANCE_MANAGER = "GROUP_FINANCE_MANAGER"
    GROUP_ANALYTICS_VIEWER = "GROUP_ANALYTICS_VIEWER"
    GROUP_IT_ADMIN = "GROUP_IT_ADMIN"


# ---------------------------------------------------------------------------
# Institution-Level Roles (18)
# ---------------------------------------------------------------------------


class InstitutionRole(StrEnum):
    """Roles within a single institution (college / school / coaching)."""

    # Administration (3)
    INSTITUTION_OWNER = "INSTITUTION_OWNER"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    BRANCH_MANAGER = "BRANCH_MANAGER"

    # Academic (5)
    ACADEMIC_HEAD = "ACADEMIC_HEAD"
    DEPARTMENT_HEAD = "DEPARTMENT_HEAD"
    TEACHER = "TEACHER"
    EXAM_COORDINATOR = "EXAM_COORDINATOR"
    LAB_INSTRUCTOR = "LAB_INSTRUCTOR"

    # Content (4)
    INST_CONTENT_CREATOR = "INST_CONTENT_CREATOR"
    INST_CONTENT_REVIEWER = "INST_CONTENT_REVIEWER"
    INST_TEST_CREATOR = "INST_TEST_CREATOR"
    INST_NOTES_MANAGER = "INST_NOTES_MANAGER"

    # Student Management (3)
    BATCH_MANAGER = "BATCH_MANAGER"
    COUNSELOR = "COUNSELOR"
    ADMISSION_OFFICER = "ADMISSION_OFFICER"

    # Operations (3)
    INST_FINANCE_MANAGER = "INST_FINANCE_MANAGER"
    INST_SUPPORT_AGENT = "INST_SUPPORT_AGENT"
    INST_ANALYTICS_VIEWER = "INST_ANALYTICS_VIEWER"


# ---------------------------------------------------------------------------
# End-User Roles (3)
# ---------------------------------------------------------------------------


class EndUserRole(StrEnum):
    """Roles for students, parents, and guests."""

    STUDENT = "STUDENT"
    PARENT = "PARENT"
    GUEST = "GUEST"


# ---------------------------------------------------------------------------
# Convenience collections
# ---------------------------------------------------------------------------

PLATFORM_ROLES: list[str] = [r.value for r in PlatformRole]
GROUP_ROLES: list[str] = [r.value for r in GroupRole]
INSTITUTION_ROLES: list[str] = [r.value for r in InstitutionRole]
END_USER_ROLES: list[str] = [r.value for r in EndUserRole]
ALL_ROLES: list[str] = PLATFORM_ROLES + GROUP_ROLES + INSTITUTION_ROLES + END_USER_ROLES


# ---------------------------------------------------------------------------
# Department mapping for platform roles
# ---------------------------------------------------------------------------

PLATFORM_ROLE_DEPARTMENTS: dict[str, str] = {
    # Super Administration
    PlatformRole.SUPER_ADMIN: "Super Administration",
    PlatformRole.PLATFORM_ADMIN: "Super Administration",
    PlatformRole.OPERATIONS_MANAGER: "Super Administration",
    # Engineering & Infrastructure
    PlatformRole.INFRA_ADMIN: "Engineering & Infrastructure",
    PlatformRole.API_MANAGER: "Engineering & Infrastructure",
    PlatformRole.SECURITY_ADMIN: "Engineering & Infrastructure",
    # Product & Catalog
    PlatformRole.PRODUCT_MANAGER: "Product & Catalog",
    PlatformRole.CATALOG_MANAGER: "Product & Catalog",
    PlatformRole.WHITE_LABEL_MANAGER: "Product & Catalog",
    # Sales & BD
    PlatformRole.SALES_MANAGER: "Sales & Business Development",
    PlatformRole.SALES_EXECUTIVE: "Sales & Business Development",
    PlatformRole.ACCOUNT_MANAGER: "Sales & Business Development",
    PlatformRole.PARTNERSHIP_MANAGER: "Sales & Business Development",
    PlatformRole.MARKETING_MANAGER: "Sales & Business Development",
    # Customer Operations
    PlatformRole.SUPPORT_MANAGER: "Customer Operations",
    PlatformRole.SUPPORT_AGENT: "Customer Operations",
    PlatformRole.ONBOARDING_SPECIALIST: "Customer Operations",
    PlatformRole.CUSTOMER_SUCCESS_MANAGER: "Customer Operations",
    # Curriculum & Board
    PlatformRole.CURRICULUM_MANAGER: "Curriculum & Board Management",
    PlatformRole.EXAM_PATTERN_MANAGER: "Curriculum & Board Management",
    PlatformRole.SUBJECT_MATTER_EXPERT: "Curriculum & Board Management",
    # MCQ / Question Bank
    PlatformRole.QUESTION_CREATOR: "MCQ / Question Bank",
    PlatformRole.QUESTION_REVIEWER: "MCQ / Question Bank",
    PlatformRole.QUESTION_BANK_MANAGER: "MCQ / Question Bank",
    PlatformRole.QUESTION_IMPORTER: "MCQ / Question Bank",
    # Notes & Study Material
    PlatformRole.NOTES_CREATOR: "Notes & Study Material",
    PlatformRole.NOTES_REVIEWER: "Notes & Study Material",
    PlatformRole.STUDY_MATERIAL_MANAGER: "Notes & Study Material",
    PlatformRole.PREVIOUS_YEAR_PAPER_MANAGER: "Notes & Study Material",
    # Video Content
    PlatformRole.VIDEO_CREATOR: "Video Content",
    PlatformRole.VIDEO_REVIEWER: "Video Content",
    PlatformRole.VIDEO_PLAYLIST_MANAGER: "Video Content",
    # Test & Assessment
    PlatformRole.TEST_CREATOR: "Test & Assessment",
    PlatformRole.TEST_REVIEWER: "Test & Assessment",
    PlatformRole.TEST_SCHEDULER: "Test & Assessment",
    PlatformRole.TEST_ANALYTICS_MANAGER: "Test & Assessment",
    # Current Affairs
    PlatformRole.CURRENT_AFFAIRS_EDITOR: "Current Affairs & Daily Content",
    PlatformRole.EDITORIAL_MANAGER: "Current Affairs & Daily Content",
    # Finance & Subscription
    PlatformRole.FINANCE_ADMIN: "Finance & Subscription",
    PlatformRole.SUBSCRIPTION_MANAGER: "Finance & Subscription",
    PlatformRole.PAYOUT_MANAGER: "Finance & Subscription",
    # Analytics & Reporting
    PlatformRole.DATA_ANALYST: "Analytics & Reporting",
    PlatformRole.REPORT_TEMPLATE_MANAGER: "Analytics & Reporting",
    PlatformRole.LEADERBOARD_MANAGER: "Analytics & Reporting",
    # Communication
    PlatformRole.NOTIFICATION_ADMIN: "Communication & Notifications",
    PlatformRole.BROADCAST_MANAGER: "Communication & Notifications",
    PlatformRole.COMMUNITY_MODERATOR: "Communication & Notifications",
    # Compliance & Legal
    PlatformRole.COMPLIANCE_OFFICER: "Compliance & Legal",
    PlatformRole.ABUSE_PREVENTION_MANAGER: "Compliance & Legal",
    # Data Operations
    PlatformRole.DATA_OPERATIONS_MANAGER: "Data Operations",
    PlatformRole.CONTENT_MIGRATION_SPECIALIST: "Data Operations",
}


# Super admin roles — used for access checks
SUPER_ADMIN_ROLES: set[str] = {
    PlatformRole.SUPER_ADMIN,
}

ADMIN_ROLES: set[str] = {
    PlatformRole.SUPER_ADMIN,
    PlatformRole.PLATFORM_ADMIN,
    PlatformRole.OPERATIONS_MANAGER,
}
