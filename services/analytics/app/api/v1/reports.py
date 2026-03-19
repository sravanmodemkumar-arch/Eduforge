"""Report generation and retrieval endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.report import (
    CustomReportRequest,
    ReportResponse,
)
from app.services.report_service import ReportService, get_report_service

router = APIRouter()


@router.get(
    "/attendance",
    response_model=ReportResponse,
    summary="Get attendance report",
)
async def get_attendance_report(
    institution_id: UUID = Query(...),
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    class_id: Optional[UUID] = Query(None),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """Generate or retrieve a cached attendance report for the given
    institution and date range.
    """
    return await service.generate_attendance_report(
        institution_id=institution_id,
        start_date=start_date,
        end_date=end_date,
        class_id=class_id,
    )


@router.get(
    "/exam-performance",
    response_model=ReportResponse,
    summary="Get exam performance report",
)
async def get_exam_performance(
    institution_id: UUID = Query(...),
    exam_id: Optional[UUID] = Query(None),
    subject: Optional[str] = Query(None, max_length=255),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """Generate or retrieve a cached exam performance report."""
    return await service.generate_exam_performance_report(
        institution_id=institution_id,
        exam_id=exam_id,
        subject=subject,
    )


@router.get(
    "/fee-collection",
    response_model=ReportResponse,
    summary="Get fee collection report",
)
async def get_fee_collection(
    institution_id: UUID = Query(...),
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """Generate or retrieve a cached fee-collection summary report."""
    return await service.generate_fee_collection_report(
        institution_id=institution_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.post(
    "/custom",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a custom report",
)
async def generate_custom_report(
    payload: CustomReportRequest,
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """Submit a custom report request with arbitrary parameters.

    The report is generated asynchronously; poll the returned report ID
    for status updates.
    """
    return await service.generate_custom_report(payload)
