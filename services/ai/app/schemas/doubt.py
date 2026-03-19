"""Pydantic schemas for doubts and recommendations."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Doubt schemas ──────────────────────────────────────────────────────

class DoubtCreate(BaseModel):
    """Payload for submitting a new doubt."""

    student_id: UUID
    institution_id: UUID
    subject: str = Field(..., max_length=255)
    question_text: str = Field(..., min_length=1, max_length=5000)
    image_r2_key: Optional[str] = Field(None, max_length=512)


class DoubtResponse(BaseModel):
    """Public representation of a resolved (or pending) doubt."""

    id: UUID
    student_id: UUID
    institution_id: UUID
    subject: str
    question_text: str
    image_r2_key: Optional[str] = None
    ai_response: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DoubtListResponse(BaseModel):
    """Paginated list of doubts."""

    items: list[DoubtResponse]
    total: int
    page: int
    page_size: int


# ── Recommendation schemas ────────────────────────────────────────────

class StudyPlanItem(BaseModel):
    """Single item in a study plan."""

    topic: str
    priority: str = Field(..., pattern="^(high|medium|low)$")
    estimated_hours: float = Field(..., gt=0)
    resources: list[str] = Field(default_factory=list)
    rationale: str


class StudyPlanResponse(BaseModel):
    """AI-generated study plan for a student."""

    student_id: UUID
    subject: str
    items: list[StudyPlanItem]
    summary: str


class WeakTopic(BaseModel):
    """A topic identified as needing improvement."""

    topic: str
    subject: str
    doubt_count: int = Field(..., ge=0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    suggestion: str


class WeakTopicsResponse(BaseModel):
    """Weak-topic analysis result."""

    student_id: UUID
    topics: list[WeakTopic]
