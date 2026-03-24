"""Progress tracking API endpoints."""

from fastapi import APIRouter, HTTPException

from app.models import ProfileUpdateRequest
from app.services import progress_service

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/{student_id}")
async def get_progress(student_id: str):
    """Get a student's progress summary."""
    return await progress_service.get_student_summary(student_id)


@router.post("/{student_id}/difficulty")
async def recommend_difficulty(student_id: str, subject: str, topic: str):
    """Get an AI-recommended difficulty adjustment for a topic."""
    difficulty, reason = await progress_service.recommend_difficulty(
        student_id, subject, topic
    )
    return {"difficulty": difficulty.value, "reason": reason}


@router.get("/{student_id}/profile")
async def get_profile(student_id: str):
    """Get the student profile."""
    return await progress_service.get_profile(student_id)


@router.put("/{student_id}/profile")
async def update_profile(student_id: str, update: ProfileUpdateRequest):
    """Update the student profile."""
    await progress_service.update_profile(student_id, update)
    return await progress_service.get_profile(student_id)


@router.get("/{student_id}/recommendations")
async def get_recommendations(student_id: str):
    """Get AI-powered next-best learning activity recommendations."""
    try:
        recs = await progress_service.get_recommendations(student_id)
        return {"recommendations": [r.model_dump() for r in recs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
