"""Quiz generation and grading service."""

import json
import logging

from app.azure_client import get_openai_client
from app.config import get_settings
from app.models import (
    Difficulty,
    QuizQuestion,
    QuizRequest,
    QuizResult,
    QuizSubmission,
)
from app.prompts import QUIZ_GENERATION_PROMPT

logger = logging.getLogger(__name__)

# In-memory quiz store  (question_id -> QuizQuestion)
_questions: dict[str, QuizQuestion] = {}


async def generate_quiz(request: QuizRequest) -> list[QuizQuestion]:
    """Generate quiz questions using Azure OpenAI."""
    client = get_openai_client()
    settings = get_settings()

    prompt = QUIZ_GENERATION_PROMPT.format(
        num_questions=request.num_questions,
        subject=request.subject,
        topic=request.topic,
        difficulty=request.difficulty.value,
    )

    response = await client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)

    questions: list[QuizQuestion] = []
    for item in data.get("questions", []):
        q = QuizQuestion(
            question=item["question"],
            choices=item["choices"],
            correct_index=item["correct_index"],
            explanation=item["explanation"],
            difficulty=request.difficulty,
        )
        _questions[q.id] = q
        questions.append(q)

    logger.info("Generated %d questions for %s / %s", len(questions), request.subject, request.topic)
    return questions


def grade_answer(submission: QuizSubmission) -> QuizResult:
    """Grade a single quiz answer."""
    question = _questions.get(submission.question_id)
    if question is None:
        raise ValueError(f"Unknown question: {submission.question_id}")

    correct = submission.selected_index == question.correct_index

    return QuizResult(
        question_id=submission.question_id,
        correct=correct,
        correct_index=question.correct_index,
        explanation=question.explanation,
    )
