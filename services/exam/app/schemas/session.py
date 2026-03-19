from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────────────────────
class SessionStartRequest(BaseModel):
    test_id: uuid.UUID
    device_fingerprint: str | None = None


class SessionSubmitRequest(BaseModel):
    answers: dict[str, str] = Field(
        ...,
        description="Map of question index/id to selected option id, e.g. {'1': 'A', '2': 'C'}",
    )
    time_taken_seconds: int = Field(..., ge=0)
    submit_source: str = Field("MANUAL", pattern="^(MANUAL|AUTO_TIMER|FORCE_SUBMIT)$")


# ── Response ─────────────────────────────────────────────────────────────────
class SessionStartResponse(BaseModel):
    session_id: uuid.UUID
    test_r2_url: str
    salt: str
    duration_seconds: int
    started_at: datetime


class SessionSubmitResponse(BaseModel):
    session_id: uuid.UUID
    status: str
    submitted_at: datetime
    message: str = "Answers submitted successfully. Scoring in progress."


class SessionRecoverResponse(BaseModel):
    session_id: uuid.UUID
    time_remaining: int = Field(..., description="Remaining time in seconds")
    status: str
    started_at: datetime


class SessionStatusResponse(BaseModel):
    session_id: uuid.UUID
    status: str
    started_at: datetime
    duration_seconds: int
    answers_received: bool
