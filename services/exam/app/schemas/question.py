from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Sub-models ───────────────────────────────────────────────────────────────
class OptionItem(BaseModel):
    id: str = Field(..., max_length=8, description="Option identifier, e.g. 'A', 'B'")
    text_en: str
    text_hi: str | None = None


# ── Create / Update ─────────────────────────────────────────────────────────
class QuestionCreate(BaseModel):
    institution_id: uuid.UUID
    subject: str = Field(..., max_length=128)
    topic: str = Field(..., max_length=256)
    difficulty: str = Field("MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")
    question_text_en: str
    question_text_hi: str | None = None
    options: list[OptionItem]
    correct_option_id: str = Field(..., max_length=8)
    explanation_en: str | None = None
    explanation_hi: str | None = None
    marks: float = 1.0
    negative_marks: float = 0.0
    tags: list[str] | None = None


class QuestionUpdate(BaseModel):
    subject: str | None = Field(None, max_length=128)
    topic: str | None = Field(None, max_length=256)
    difficulty: str | None = Field(None, pattern="^(EASY|MEDIUM|HARD)$")
    question_text_en: str | None = None
    question_text_hi: str | None = None
    options: list[OptionItem] | None = None
    correct_option_id: str | None = Field(None, max_length=8)
    explanation_en: str | None = None
    explanation_hi: str | None = None
    marks: float | None = None
    negative_marks: float | None = None
    tags: list[str] | None = None


class QuestionBulkImport(BaseModel):
    questions: list[QuestionCreate]


# ── Response ─────────────────────────────────────────────────────────────────
class QuestionResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    subject: str
    topic: str
    difficulty: str
    question_text_en: str
    question_text_hi: str | None = None
    options: Any
    correct_option_id: str
    explanation_en: str | None = None
    explanation_hi: str | None = None
    marks: float
    negative_marks: float
    status: str
    created_by: uuid.UUID
    approved_by: uuid.UUID | None = None
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    items: list[QuestionResponse]
    total: int
    page: int
    page_size: int


class BulkImportResponse(BaseModel):
    created_count: int
    errors: list[dict[str, Any]]
