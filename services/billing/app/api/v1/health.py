"""Health-check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, status

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Service health check",
)
async def health_check() -> dict[str, str]:
    """Return a simple health status for the billing service."""
    return {"status": "healthy", "service": "billing"}
