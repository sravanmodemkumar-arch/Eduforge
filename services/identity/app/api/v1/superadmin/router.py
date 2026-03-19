"""Main Super Admin router — aggregates all SA sub-routers under /api/v1/sa."""

from __future__ import annotations

from fastapi import APIRouter

from . import (
    announcements,
    approvals,
    config,
    dashboard,
    emergency,
    incidents,
    institutions,
    security,
    subscriptions,
    users,
)

router = APIRouter(prefix="/api/v1/sa")

router.include_router(dashboard.router)
router.include_router(institutions.router)
router.include_router(users.router)
router.include_router(subscriptions.router)
router.include_router(config.router)
router.include_router(security.router)
router.include_router(incidents.router)
router.include_router(announcements.router)
router.include_router(approvals.router)
router.include_router(emergency.router)
