from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientPermissionsError, ResultNotFoundError
from app.main import get_db
from app.models.result import Result
from app.schemas.result import ResultListResponse, ResultResponse

router = APIRouter()


# ── GET /results/test/{test_id}/me ───────────────────────────────────────────
@router.get(
    "/results/test/{test_id}/me",
    response_model=ResultResponse,
    summary="Get my result for a specific test",
)
async def get_my_result(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
) -> Result:
    student_id = uuid.UUID(x_user_id)
    result = await db.execute(
        select(Result).where(
            Result.test_id == test_id,
            Result.student_id == student_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise ResultNotFoundError("No result found for this test")
    return row


# ── GET /results/test/{test_id} ─────────────────────────────────────────────
@router.get(
    "/results/test/{test_id}",
    response_model=ResultListResponse,
    summary="Get all results for a test (staff only)",
)
async def get_test_results(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    x_user_role: str = Header("student"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    if x_user_role not in ("staff", "admin", "superadmin"):
        raise InsufficientPermissionsError("Staff or admin role required")

    count_stmt = select(func.count(Result.id)).where(Result.test_id == test_id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    stmt = (
        select(Result)
        .where(Result.test_id == test_id)
        .order_by(Result.rank.asc().nullslast())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return {"items": items, "total": total}


# ── GET /results/student/{student_id} ────────────────────────────────────────
@router.get(
    "/results/student/{student_id}",
    response_model=ResultListResponse,
    summary="Get all results for a student",
)
async def get_student_results(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header("student"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    requester_id = uuid.UUID(x_user_id)

    # Students can only view their own results
    if x_user_role == "student" and requester_id != student_id:
        raise InsufficientPermissionsError("Students can only view their own results")

    count_stmt = select(func.count(Result.id)).where(Result.student_id == student_id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    stmt = (
        select(Result)
        .where(Result.student_id == student_id)
        .order_by(Result.computed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return {"items": items, "total": total}
