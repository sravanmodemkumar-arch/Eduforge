from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReportRequest(BaseModel):
    institution_id: UUID
    report_type: str
    parameters: dict = {}


class ReportResponse(BaseModel):
    id: UUID
    institution_id: UUID
    report_type: str
    status: str
    r2_url: str | None = None
    generated_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
