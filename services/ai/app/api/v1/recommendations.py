"""Recommendation endpoints for study plans and weak-topic analysis."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.schemas.doubt import StudyPlanResponse, WeakTopicsResponse
from app.services.recommendation_service import (
    RecommendationService,
    get_recommendation_service,
)

router = APIRouter()


@router.get(
    "/study-plan",
    response_model=StudyPlanResponse,
    summary="Generate a personalised study plan",
)
async def get_study_plan(
    student_id: UUID = Query(..., description="Student UUID"),
    subject: str = Query(..., max_length=255, description="Subject name"),
    service: RecommendationService = Depends(get_recommendation_service),
) -> StudyPlanResponse:
    """Build an AI-generated study plan based on the student's doubt history
    and performance data.
    """
    return await service.generate_study_plan(student_id, subject)


@router.get(
    "/weak-topics",
    response_model=WeakTopicsResponse,
    summary="Identify weak topics for a student",
)
async def get_weak_topics(
    student_id: UUID = Query(..., description="Student UUID"),
    subject: str = Query(None, max_length=255, description="Optional subject filter"),
    service: RecommendationService = Depends(get_recommendation_service),
) -> WeakTopicsResponse:
    """Analyse the student's doubt history and return topics that need
    additional attention, ranked by frequency and recency.
    """
    return await service.identify_weak_topics(student_id, subject)
