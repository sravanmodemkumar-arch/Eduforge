from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SessionNotFoundError
from app.main import get_db
from app.models.exam_session import ExamSession
from app.schemas.session import (
    SessionRecoverResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionStatusResponse,
    SessionSubmitRequest,
    SessionSubmitResponse,
)
from app.services.session_service import SessionService

router = APIRouter()


# ── POST /exam/sessions/start ────────────────────────────────────────────────
@router.post(
    "/exam/sessions/start",
    response_model=SessionStartResponse,
    status_code=201,
    summary="Start an exam session (Lambda call #1 of 2)",
)
async def start_session(
    body: SessionStartRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
    x_institution_id: str = Header(...),
) -> dict:
    student_id = uuid.UUID(x_user_id)
    institution_id = uuid.UUID(x_institution_id)
    ip_address = request.client.host if request.client else None

    service = SessionService(db)
    return await service.start_session(
        student_id=student_id,
        institution_id=institution_id,
        test_id=body.test_id,
        device_fingerprint=body.device_fingerprint,
        ip_address=ip_address,
    )


# ── POST /exam/sessions/{id}/submit ─────────────────────────────────────────
@router.post(
    "/exam/sessions/{session_id}/submit",
    response_model=SessionSubmitResponse,
    summary="Submit all answers at once (Lambda call #2 of 2)",
)
async def submit_session(
    session_id: uuid.UUID,
    body: SessionSubmitRequest,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
) -> dict:
    student_id = uuid.UUID(x_user_id)
    service = SessionService(db)
    return await service.submit_session(
        session_id=session_id,
        student_id=student_id,
        answers=body.answers,
        time_taken_seconds=body.time_taken_seconds,
        submit_source=body.submit_source,
    )


# ── GET /exam/sessions/{id}/recover ─────────────────────────────────────────
@router.get(
    "/exam/sessions/{session_id}/recover",
    response_model=SessionRecoverResponse,
    summary="Crash recovery - get remaining time so browser can resume from IndexedDB",
)
async def recover_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
) -> dict:
    student_id = uuid.UUID(x_user_id)
    service = SessionService(db)
    return await service.recover_session(session_id=session_id, student_id=student_id)


# ── GET /exam/sessions/{id}/status ───────────────────────────────────────────
@router.get(
    "/exam/sessions/{session_id}/status",
    response_model=SessionStatusResponse,
    summary="Check exam session status",
)
async def get_session_status(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise SessionNotFoundError(str(session_id))

    return {
        "session_id": session.id,
        "status": session.status.value,
        "started_at": session.started_at,
        "duration_seconds": session.duration_seconds,
        "answers_received": session.answers_received,
    }
