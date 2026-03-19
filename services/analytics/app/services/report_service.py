"""Service layer for report generation and dashboard aggregation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.exceptions import (
    ReportGenerationError,
    ReportNotFoundError,
    UpstreamServiceError,
)
from app.models.report import Report
from app.schemas.report import (
    ChartDataPoint,
    ChartSeries,
    CustomReportRequest,
    DashboardResponse,
    KPIMetric,
    ReportResponse,
)

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class ReportService:
    """Handles report generation, caching, and dashboard aggregation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._http = httpx.AsyncClient(timeout=30.0)

    # ── Attendance ─────────────────────────────────────────────────────

    async def generate_attendance_report(
        self,
        *,
        institution_id: UUID,
        start_date: str,
        end_date: str,
        class_id: Optional[UUID] = None,
    ) -> ReportResponse:
        """Generate an attendance summary report."""
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if class_id:
            params["class_id"] = str(class_id)

        return await self._create_report(
            institution_id=institution_id,
            report_type="attendance",
            parameters=params,
        )

    # ── Exam performance ───────────────────────────────────────────────

    async def generate_exam_performance_report(
        self,
        *,
        institution_id: UUID,
        exam_id: Optional[UUID] = None,
        subject: Optional[str] = None,
    ) -> ReportResponse:
        """Generate an exam performance report."""
        params: dict[str, Any] = {}
        if exam_id:
            params["exam_id"] = str(exam_id)
        if subject:
            params["subject"] = subject

        return await self._create_report(
            institution_id=institution_id,
            report_type="exam_performance",
            parameters=params,
        )

    # ── Fee collection ─────────────────────────────────────────────────

    async def generate_fee_collection_report(
        self,
        *,
        institution_id: UUID,
        start_date: str,
        end_date: str,
    ) -> ReportResponse:
        """Generate a fee-collection summary report."""
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        return await self._create_report(
            institution_id=institution_id,
            report_type="fee_collection",
            parameters=params,
        )

    # ── Custom reports ─────────────────────────────────────────────────

    async def generate_custom_report(
        self, payload: CustomReportRequest
    ) -> ReportResponse:
        """Create a custom report entry (generation happens asynchronously)."""
        return await self._create_report(
            institution_id=payload.institution_id,
            report_type=payload.report_type,
            parameters=payload.parameters,
        )

    # ── Dashboards ─────────────────────────────────────────────────────

    async def get_institution_dashboard(
        self, institution_id: UUID
    ) -> DashboardResponse:
        """Aggregate KPIs and chart data for an institution dashboard."""
        attendance_data = await self._fetch_upstream(
            f"{settings.attendance_service_url}/api/v1/attendance/stats",
            params={"institution_id": str(institution_id)},
        )
        assessment_data = await self._fetch_upstream(
            f"{settings.assessment_service_url}/api/v1/assessments/stats",
            params={"institution_id": str(institution_id)},
        )
        fee_data = await self._fetch_upstream(
            f"{settings.fee_service_url}/api/v1/fees/stats",
            params={"institution_id": str(institution_id)},
        )

        kpis = self._build_institution_kpis(attendance_data, assessment_data, fee_data)
        charts = self._build_institution_charts(attendance_data, assessment_data)

        return DashboardResponse(
            entity_id=institution_id,
            kpis=kpis,
            charts=charts,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_b2b_dashboard(self, partner_id: UUID) -> DashboardResponse:
        """Aggregate KPIs across all institutions for a B2B partner."""
        kpis = [
            KPIMetric(label="Total Institutions", value=0, unit="count"),
            KPIMetric(label="Average Attendance", value=0, unit="%"),
            KPIMetric(label="Average Exam Score", value=0, unit="%"),
            KPIMetric(label="Fee Collection Rate", value=0, unit="%"),
        ]
        charts: list[ChartSeries] = []

        return DashboardResponse(
            entity_id=partner_id,
            kpis=kpis,
            charts=charts,
            generated_at=datetime.now(timezone.utc),
        )

    # ── Internal helpers ───────────────────────────────────────────────

    async def _create_report(
        self,
        *,
        institution_id: UUID,
        report_type: str,
        parameters: dict[str, Any],
    ) -> ReportResponse:
        """Persist a new report record and return its public representation."""
        report = Report(
            institution_id=institution_id,
            report_type=report_type,
            parameters=parameters,
            status="pending",
        )
        self._session.add(report)
        await self._session.flush()

        try:
            report.status = "completed"
            report.generated_at = datetime.now(timezone.utc)
        except Exception:
            logger.exception("Report generation failed for %s", report.id)
            report.status = "failed"
            await self._session.commit()
            raise ReportGenerationError(report_id=str(report.id))

        await self._session.commit()
        await self._session.refresh(report)
        return ReportResponse.model_validate(report)

    async def _fetch_upstream(
        self, url: str, params: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Call an upstream EduForge microservice and return its JSON payload."""
        try:
            resp = await self._http.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Upstream %s returned %s", url, exc.response.status_code)
            raise UpstreamServiceError(service_url=url)
        except httpx.RequestError as exc:
            logger.error("Failed to reach upstream %s: %s", url, exc)
            raise UpstreamServiceError(service_url=url)

    @staticmethod
    def _build_institution_kpis(
        attendance: dict[str, Any],
        assessment: dict[str, Any],
        fee: dict[str, Any],
    ) -> list[KPIMetric]:
        """Map upstream data into dashboard KPI metrics."""
        return [
            KPIMetric(
                label="Attendance Rate",
                value=attendance.get("average_rate", 0),
                unit="%",
                trend=attendance.get("trend"),
            ),
            KPIMetric(
                label="Average Exam Score",
                value=assessment.get("average_score", 0),
                unit="%",
                trend=assessment.get("trend"),
            ),
            KPIMetric(
                label="Fee Collection Rate",
                value=fee.get("collection_rate", 0),
                unit="%",
                trend=fee.get("trend"),
            ),
            KPIMetric(
                label="Total Students",
                value=attendance.get("total_students", 0),
                unit="count",
            ),
        ]

    @staticmethod
    def _build_institution_charts(
        attendance: dict[str, Any],
        assessment: dict[str, Any],
    ) -> list[ChartSeries]:
        """Map upstream data into chart series for the dashboard."""
        charts: list[ChartSeries] = []

        monthly_attendance = attendance.get("monthly", [])
        if monthly_attendance:
            charts.append(
                ChartSeries(
                    name="Monthly Attendance",
                    data=[
                        ChartDataPoint(label=m.get("month", ""), value=m.get("rate", 0))
                        for m in monthly_attendance
                    ],
                )
            )

        subject_scores = assessment.get("by_subject", [])
        if subject_scores:
            charts.append(
                ChartSeries(
                    name="Scores by Subject",
                    data=[
                        ChartDataPoint(
                            label=s.get("subject", ""), value=s.get("average", 0)
                        )
                        for s in subject_scores
                    ],
                )
            )

        return charts


async def get_report_service() -> ReportService:
    """FastAPI dependency that yields a ``ReportService`` per request."""
    async with async_session() as session:
        yield ReportService(session)
