"""Dashboard data endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.schemas.report import DashboardResponse
from app.services.report_service import ReportService, get_report_service

router = APIRouter()


@router.get(
    "/institution",
    response_model=DashboardResponse,
    summary="Get institution dashboard data",
)
async def get_institution_dashboard(
    institution_id: UUID = Query(...),
    service: ReportService = Depends(get_report_service),
) -> DashboardResponse:
    """Return aggregated KPI data for a single institution's dashboard,
    including attendance rates, exam averages, fee collection status,
    and recent trends.
    """
    return await service.get_institution_dashboard(institution_id)


@router.get(
    "/b2b",
    response_model=DashboardResponse,
    summary="Get B2B partner dashboard data",
)
async def get_b2b_dashboard(
    partner_id: UUID = Query(..., description="B2B partner UUID"),
    service: ReportService = Depends(get_report_service),
) -> DashboardResponse:
    """Return aggregated analytics across all institutions managed by a
    B2B partner, including comparative metrics and overall performance.
    """
    return await service.get_b2b_dashboard(partner_id)
