"""Doubt resolution endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.doubt import (
    DoubtCreate,
    DoubtListResponse,
    DoubtResponse,
)
from app.services.doubt_service import DoubtService, get_doubt_service

router = APIRouter()


@router.post(
    "",
    response_model=DoubtResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a doubt for AI resolution",
)
async def submit_doubt(
    payload: DoubtCreate,
    service: DoubtService = Depends(get_doubt_service),
) -> DoubtResponse:
    """Submit a student doubt to be resolved by the AI engine.

    The AI processes the question (and optional image) and returns
    a detailed, educationally-oriented explanation.
    """
    doubt = await service.create_doubt(payload)
    return doubt


@router.get(
    "/{doubt_id}",
    response_model=DoubtResponse,
    summary="Retrieve a doubt by ID",
)
async def get_doubt(
    doubt_id: UUID,
    service: DoubtService = Depends(get_doubt_service),
) -> DoubtResponse:
    """Return a single doubt and its AI response."""
    doubt = await service.get_doubt_by_id(doubt_id)
    if doubt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doubt {doubt_id} not found",
        )
    return doubt


@router.get(
    "",
    response_model=DoubtListResponse,
    summary="List doubts with filtering",
)
async def list_doubts(
    student_id: Optional[UUID] = Query(None),
    institution_id: Optional[UUID] = Query(None),
    subject: Optional[str] = Query(None, max_length=255),
    status_filter: Optional[str] = Query(
        None, alias="status", pattern="^(pending|processing|resolved|failed)$"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: DoubtService = Depends(get_doubt_service),
) -> DoubtListResponse:
    """Return a paginated list of doubts with optional filters."""
    doubts, total = await service.list_doubts(
        student_id=student_id,
        institution_id=institution_id,
        subject=subject,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    return DoubtListResponse(items=doubts, total=total, page=page, page_size=page_size)
