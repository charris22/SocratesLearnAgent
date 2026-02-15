"""Progress tracking API endpoints."""

from fastapi import APIRouter

from app.services import progress_service

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/{student_id}")
async def get_progress(student_id: str):
    """Get a student's progress summary."""
    return progress_service.get_student_summary(student_id)


@router.post("/{student_id}/difficulty")
async def recommend_difficulty(student_id: str, subject: str, topic: str):
    """Get an AI-recommended difficulty adjustment for a topic."""
    difficulty, reason = await progress_service.recommend_difficulty(
        student_id, subject, topic
    )
    return {"difficulty": difficulty.value, "reason": reason}
