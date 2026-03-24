"""Quiz generation and grading service."""

import json
import logging

from app.azure_client import get_openai_client
from app import database as db
from app.config import get_settings
from app.models import (
    CognitiveLevel,
    Difficulty,
    QuizQuestion,
    QuizRequest,
    QuizResult,
    QuizSubmission,
)
from app.prompts import QUIZ_GENERATION_PROMPT

logger = logging.getLogger(__name__)


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
        # Parse cognitive level safely
        cog_raw = item.get("cognitive_level", "application").lower()
        try:
            cog = CognitiveLevel(cog_raw)
        except ValueError:
            cog = CognitiveLevel.APPLICATION

        q = QuizQuestion(
            question=item["question"],
            choices=item["choices"],
            correct_index=item["correct_index"],
            explanation=item["explanation"],
            difficulty=request.difficulty,
            concept=item.get("concept", request.topic),
            cognitive_level=cog,
        )
        await db.save_quiz_question({
            "id": q.id,
            "question": q.question,
            "choices": q.choices,
            "correct_index": q.correct_index,
            "explanation": q.explanation,
            "difficulty": q.difficulty.value,
            "concept": q.concept,
            "cognitive_level": q.cognitive_level.value,
        })
        questions.append(q)

    logger.info("Generated %d questions for %s / %s", len(questions), request.subject, request.topic)
    return questions


async def grade_answer(submission: QuizSubmission) -> QuizResult:
    """Grade a single quiz answer."""
    row = await db.get_quiz_question(submission.question_id)
    if row is None:
        raise ValueError(f"Unknown question: {submission.question_id}")

    question = QuizQuestion(
        id=row["id"],
        question=row["question"],
        choices=row["choices"],
        correct_index=row["correct_index"],
        explanation=row["explanation"],
        difficulty=Difficulty(row["difficulty"]),
        concept=row.get("concept", ""),
        cognitive_level=CognitiveLevel(row.get("cognitive_level", "application")),
    )

    correct = submission.selected_index == question.correct_index

    recommendation = ""
    if not correct:
        recommendation = f"Review the concept: {question.concept}. {question.explanation}"

    return QuizResult(
        question_id=submission.question_id,
        correct=correct,
        correct_index=question.correct_index,
        explanation=question.explanation,
        concept=question.concept,
        recommendation=recommendation,
    ), question
