from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientPermissionsError, QuestionNotFoundError
from app.main import get_db
from app.models.question import DifficultyLevel, Question, QuestionStatus
from app.schemas.question import (
    BulkImportResponse,
    QuestionBulkImport,
    QuestionCreate,
    QuestionListResponse,
    QuestionResponse,
    QuestionUpdate,
)

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────────
def _parse_user_headers(
    x_user_id: str = Header(...),
    x_user_role: str = Header("student"),
    x_institution_id: str = Header(...),
) -> dict[str, Any]:
    return {
        "user_id": uuid.UUID(x_user_id),
        "role": x_user_role,
        "institution_id": uuid.UUID(x_institution_id),
    }


def _require_staff(claims: dict[str, Any]) -> None:
    if claims["role"] not in ("staff", "admin", "superadmin"):
        raise InsufficientPermissionsError("Staff or admin role required")


def _require_reviewer(claims: dict[str, Any]) -> None:
    if claims["role"] not in ("reviewer", "admin", "superadmin"):
        raise InsufficientPermissionsError("Reviewer or admin role required")


# ── POST /questions/ ─────────────────────────────────────────────────────────
@router.post("/questions/", response_model=QuestionResponse, status_code=201)
async def create_question(
    body: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header("student"),
    x_institution_id: str = Header(...),
) -> Question:
    claims = _parse_user_headers(x_user_id, x_user_role, x_institution_id)
    _require_staff(claims)

    question = Question(
        institution_id=body.institution_id,
        subject=body.subject,
        topic=body.topic,
        difficulty=DifficultyLevel(body.difficulty),
        question_text_en=body.question_text_en,
        question_text_hi=body.question_text_hi,
        options=[opt.model_dump() for opt in body.options],
        correct_option_id=body.correct_option_id,
        explanation_en=body.explanation_en,
        explanation_hi=body.explanation_hi,
        marks=body.marks,
        negative_marks=body.negative_marks,
        tags=body.tags,
        created_by=claims["user_id"],
        status=QuestionStatus.DRAFT,
    )
    db.add(question)
    await db.flush()
    await db.refresh(question)
    return question


# ── GET /questions/{id} ─────────────────────────────────────────────────────
@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Question:
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise QuestionNotFoundError(str(question_id))
    return question


# ── PUT /questions/{id} ─────────────────────────────────────────────────────
@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: uuid.UUID,
    body: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header("student"),
    x_institution_id: str = Header(...),
) -> Question:
    claims = _parse_user_headers(x_user_id, x_user_role, x_institution_id)
    _require_staff(claims)

    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise QuestionNotFoundError(str(question_id))

    update_data = body.model_dump(exclude_unset=True)
    if "options" in update_data and update_data["options"] is not None:
        update_data["options"] = [opt.model_dump() if hasattr(opt, "model_dump") else opt for opt in update_data["options"]]
    if "difficulty" in update_data and update_data["difficulty"] is not None:
        update_data["difficulty"] = DifficultyLevel(update_data["difficulty"])

    for field, value in update_data.items():
        setattr(question, field, value)

    await db.flush()
    await db.refresh(question)
    return question


# ── GET /questions/ ──────────────────────────────────────────────────────────
@router.get("/questions/", response_model=QuestionListResponse)
async def list_questions(
    db: AsyncSession = Depends(get_db),
    x_institution_id: str = Header(...),
    subject: str | None = Query(None),
    topic: str | None = Query(None),
    difficulty: str | None = Query(None, pattern="^(EASY|MEDIUM|HARD)$"),
    language: str | None = Query(None, pattern="^(en|hi)$"),
    status: str | None = Query(None, pattern="^(DRAFT|REVIEW|APPROVED)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    institution_id = uuid.UUID(x_institution_id)
    stmt = select(Question).where(Question.institution_id == institution_id)
    count_stmt = select(func.count(Question.id)).where(Question.institution_id == institution_id)

    if subject:
        stmt = stmt.where(Question.subject == subject)
        count_stmt = count_stmt.where(Question.subject == subject)
    if topic:
        stmt = stmt.where(Question.topic == topic)
        count_stmt = count_stmt.where(Question.topic == topic)
    if difficulty:
        stmt = stmt.where(Question.difficulty == DifficultyLevel(difficulty))
        count_stmt = count_stmt.where(Question.difficulty == DifficultyLevel(difficulty))
    if status:
        stmt = stmt.where(Question.status == QuestionStatus(status))
        count_stmt = count_stmt.where(Question.status == QuestionStatus(status))
    if language == "hi":
        stmt = stmt.where(Question.question_text_hi.isnot(None))
        count_stmt = count_stmt.where(Question.question_text_hi.isnot(None))

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = stmt.order_by(Question.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── POST /questions/{id}/approve ─────────────────────────────────────────────
@router.post("/questions/{question_id}/approve", response_model=QuestionResponse)
async def approve_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header("student"),
    x_institution_id: str = Header(...),
) -> Question:
    claims = _parse_user_headers(x_user_id, x_user_role, x_institution_id)
    _require_reviewer(claims)

    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise QuestionNotFoundError(str(question_id))

    question.status = QuestionStatus.APPROVED
    question.approved_by = claims["user_id"]
    await db.flush()
    await db.refresh(question)
    return question


# ── POST /questions/bulk ─────────────────────────────────────────────────────
@router.post("/questions/bulk", response_model=BulkImportResponse, status_code=201)
async def bulk_import_questions(
    body: QuestionBulkImport,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header("student"),
    x_institution_id: str = Header(...),
) -> dict[str, Any]:
    claims = _parse_user_headers(x_user_id, x_user_role, x_institution_id)
    _require_staff(claims)

    created_count = 0
    errors: list[dict[str, Any]] = []

    for idx, q_data in enumerate(body.questions):
        try:
            question = Question(
                institution_id=q_data.institution_id,
                subject=q_data.subject,
                topic=q_data.topic,
                difficulty=DifficultyLevel(q_data.difficulty),
                question_text_en=q_data.question_text_en,
                question_text_hi=q_data.question_text_hi,
                options=[opt.model_dump() for opt in q_data.options],
                correct_option_id=q_data.correct_option_id,
                explanation_en=q_data.explanation_en,
                explanation_hi=q_data.explanation_hi,
                marks=q_data.marks,
                negative_marks=q_data.negative_marks,
                tags=q_data.tags,
                created_by=claims["user_id"],
                status=QuestionStatus.DRAFT,
            )
            db.add(question)
            created_count += 1
        except Exception as exc:
            errors.append({"index": idx, "error": str(exc)})

    if created_count > 0:
        await db.flush()

    return {"created_count": created_count, "errors": errors}
