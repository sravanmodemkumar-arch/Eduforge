from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ResultResponse(BaseModel):
    id: uuid.UUID
    attempt_id: uuid.UUID
    test_id: uuid.UUID
    student_id: uuid.UUID
    institution_id: uuid.UUID
    total_score: float
    max_score: float
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    percentage: float
    rank: int | None = None
    total_participants: int | None = None
    percentile: float | None = None
    section_scores: dict[str, Any] | None = None
    result_r2_key: str | None = None
    computed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ResultListResponse(BaseModel):
    items: list[ResultResponse]
    total: int


class StudentResultSummary(BaseModel):
    test_id: uuid.UUID
    test_title: str | None = None
    total_score: float
    max_score: float
    percentage: float
    rank: int | None = None
    total_participants: int | None = None
    computed_at: datetime
