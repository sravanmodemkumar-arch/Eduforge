"""Pydantic schemas for reports and dashboards."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Report schemas ─────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    """Public representation of a report."""

    id: UUID
    institution_id: UUID
    report_type: str
    parameters: dict[str, Any]
    r2_key: Optional[str] = None
    status: str
    generated_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomReportRequest(BaseModel):
    """Payload for requesting a custom report."""

    institution_id: UUID
    report_type: str = Field(..., max_length=100)
    parameters: dict[str, Any] = Field(default_factory=dict)


# ── Dashboard schemas ──────────────────────────────────────────────────

class KPIMetric(BaseModel):
    """A single key-performance-indicator value."""

    label: str
    value: float
    unit: str = ""
    trend: Optional[float] = Field(
        None,
        description="Percentage change from previous period; positive = improvement",
    )


class ChartDataPoint(BaseModel):
    """Single data point for chart rendering."""

    label: str
    value: float


class ChartSeries(BaseModel):
    """A named series of chart data points."""

    name: str
    data: list[ChartDataPoint]


class DashboardResponse(BaseModel):
    """Aggregated dashboard data."""

    entity_id: UUID = Field(..., description="Institution or partner UUID")
    kpis: list[KPIMetric]
    charts: list[ChartSeries]
    generated_at: datetime
