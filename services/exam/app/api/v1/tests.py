from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientPermissionsError, TestNotFoundError
from app.main import get_db
from app.models.result import Result
from app.models.test import Test, TestType
from app.schemas.test import (
    LeaderboardEntry,
    LeaderboardResponse,
    TestCreate,
    TestListResponse,
    TestResponse,
    TestUpdate,
)
from app.services.test_service import TestService

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


# ── POST /tests/ ─────────────────────────────────────────────────────────────
@router.post("/tests/", response_model=TestResponse, status_code=201)
async def create_test(
    body: TestCreate,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header("student"),
    x_institution_id: str = Header(...),
) -> Test:
    claims = _parse_user_headers(x_user_id, x_user_role, x_institution_id)
    _require_staff(claims)

    service = TestService(db)
    return await service.create_test(body, claims["user_id"])


# ── GET /tests/{id} ─────────────────────────────────────────────────────────
@router.get("/tests/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Test:
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise TestNotFoundError(str(test_id))
    return test


# ── GET /tests/ ──────────────────────────────────────────────────────────────
@router.get("/tests/", response_model=TestListResponse)
async def list_tests(
    db: AsyncSession = Depends(get_db),
    x_institution_id: str = Header(...),
    test_type: str | None = Query(None, pattern="^(PRACTICE|MOCK|LIVE)$"),
    is_published: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    institution_id = uuid.UUID(x_institution_id)
    stmt = select(Test).where(Test.institution_id == institution_id)
    count_stmt = select(func.count(Test.id)).where(Test.institution_id == institution_id)

    if test_type:
        stmt = stmt.where(Test.test_type == TestType(test_type))
        count_stmt = count_stmt.where(Test.test_type == TestType(test_type))
    if is_published is not None:
        stmt = stmt.where(Test.is_published == is_published)
        count_stmt = count_stmt.where(Test.is_published == is_published)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = stmt.order_by(Test.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ── POST /tests/{id}/publish ─────────────────────────────────────────────────
@router.post("/tests/{test_id}/publish", response_model=TestResponse)
async def publish_test(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: str = Header(...),
    x_user_role: str = Header("student"),
    x_institution_id: str = Header(...),
) -> Test:
    claims = _parse_user_headers(x_user_id, x_user_role, x_institution_id)
    _require_staff(claims)

    service = TestService(db)
    return await service.publish_test(test_id)


# ── GET /tests/{id}/leaderboard ──────────────────────────────────────────────
@router.get("/tests/{test_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    test_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    # Verify test exists
    test_result = await db.execute(select(Test).where(Test.id == test_id))
    if not test_result.scalar_one_or_none():
        raise TestNotFoundError(str(test_id))

    # Fetch results ordered by score descending
    stmt = (
        select(Result)
        .where(Result.test_id == test_id)
        .order_by(Result.total_score.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    results = list(result.scalars().all())

    count_stmt = select(func.count(Result.id)).where(Result.test_id == test_id)
    count_result = await db.execute(count_stmt)
    total_participants = count_result.scalar() or 0

    entries = [
        LeaderboardEntry(
            rank=idx + 1,
            student_id=r.student_id,
            total_score=r.total_score,
            percentage=r.percentage,
            time_taken_seconds=None,
        )
        for idx, r in enumerate(results)
    ]

    return {
        "test_id": test_id,
        "entries": entries,
        "total_participants": total_participants,
    }
