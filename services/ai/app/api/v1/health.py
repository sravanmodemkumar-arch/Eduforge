"""Health-check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Service health check")
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "healthy", "service": "ai"}
