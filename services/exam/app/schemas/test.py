from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Create / Update ─────────────────────────────────────────────────────────
class TestCreate(BaseModel):
    institution_id: uuid.UUID
    title: str = Field(..., max_length=512)
    description: str | None = None
    test_type: str = Field("PRACTICE", pattern="^(PRACTICE|MOCK|LIVE)$")
    duration_minutes: int = Field(..., gt=0)
    total_marks: float = Field(0.0, ge=0)
    negative_marking: bool = False
    question_ids: list[uuid.UUID] = Field(default_factory=list)
    schedule_start: datetime | None = None
    schedule_end: datetime | None = None
    settings: dict[str, Any] | None = None


class TestUpdate(BaseModel):
    title: str | None = Field(None, max_length=512)
    description: str | None = None
    test_type: str | None = Field(None, pattern="^(PRACTICE|MOCK|LIVE)$")
    duration_minutes: int | None = Field(None, gt=0)
    total_marks: float | None = Field(None, ge=0)
    negative_marking: bool | None = None
    question_ids: list[uuid.UUID] | None = None
    schedule_start: datetime | None = None
    schedule_end: datetime | None = None
    settings: dict[str, Any] | None = None


# ── Response ─────────────────────────────────────────────────────────────────
class TestResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    title: str
    description: str | None = None
    test_type: str
    duration_minutes: int
    total_marks: float
    negative_marking: bool
    question_ids: list[uuid.UUID]
    schedule_start: datetime | None = None
    schedule_end: datetime | None = None
    is_published: bool
    r2_questions_key: str | None = None
    settings: dict[str, Any] | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestListResponse(BaseModel):
    items: list[TestResponse]
    total: int
    page: int
    page_size: int


class LeaderboardEntry(BaseModel):
    rank: int
    student_id: uuid.UUID
    total_score: float
    percentage: float
    time_taken_seconds: int | None = None


class LeaderboardResponse(BaseModel):
    test_id: uuid.UUID
    entries: list[LeaderboardEntry]
    total_participants: int
