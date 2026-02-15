"""Quiz API endpoints."""

from fastapi import APIRouter, HTTPException

from app.models import QuizRequest, QuizSubmission
from app.services import quiz_service, progress_service

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/generate")
async def generate_quiz(request: QuizRequest):
    """Generate a set of quiz questions."""
    try:
        questions = await quiz_service.generate_quiz(request)
        return {"questions": [q.model_dump() for q in questions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
async def submit_answer(submission: QuizSubmission, student_id: str = "default"):
    """Submit an answer and get grading result. Also records progress."""
    try:
        result = quiz_service.grade_answer(submission)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Look up the question to get subject info for progress tracking
    question = quiz_service._questions.get(submission.question_id)
    if question:
        # Use difficulty as a proxy for topic when we don't have explicit topic
        progress_service.record_answer(
            student_id=student_id,
            subject="general",
            topic=question.difficulty.value,
            correct=result.correct,
        )

    return result.model_dump()
