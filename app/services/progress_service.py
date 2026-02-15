"""Student progress tracking and adaptive difficulty."""

import json
import logging
from datetime import UTC, datetime

from app.azure_client import get_openai_client
from app.config import get_settings
from app.models import Difficulty, StudentProfile, TopicScore
from app.prompts import DIFFICULTY_ASSESSMENT_PROMPT

logger = logging.getLogger(__name__)

# In-memory student store (swap for a database in production)
_students: dict[str, StudentProfile] = {}


def get_or_create_student(student_id: str, name: str = "Student") -> StudentProfile:
    """Retrieve an existing student profile or create a new one."""
    if student_id not in _students:
        _students[student_id] = StudentProfile(student_id=student_id, name=name)
    return _students[student_id]


def record_answer(student_id: str, subject: str, topic: str, correct: bool) -> TopicScore:
    """Record a quiz answer and update the student's topic score."""
    student = get_or_create_student(student_id)
    score = student.get_score(subject, topic)
    score.attempts += 1
    if correct:
        score.correct += 1
    score.last_attempt = datetime.now(UTC)
    return score


async def recommend_difficulty(
    student_id: str, subject: str, topic: str
) -> tuple[Difficulty, str]:
    """Use the LLM to recommend the next difficulty level based on performance."""
    student = get_or_create_student(student_id)
    score = student.get_score(subject, topic)

    # If not enough data, stay at current difficulty
    if score.attempts < 3:
        return score.current_difficulty, "Not enough attempts yet to adjust difficulty."

    client = get_openai_client()
    settings = get_settings()

    prompt = DIFFICULTY_ASSESSMENT_PROMPT.format(
        topic=topic,
        subject=subject,
        attempts=score.attempts,
        accuracy=score.accuracy,
        current_difficulty=score.current_difficulty.value,
    )

    response = await client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=256,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)

    new_difficulty = Difficulty(data.get("difficulty", score.current_difficulty.value))
    reason = data.get("reason", "")

    # Persist the new difficulty
    score.current_difficulty = new_difficulty
    logger.info(
        "Difficulty for %s/%s -> %s (%s)", subject, topic, new_difficulty.value, reason
    )

    return new_difficulty, reason


def get_student_summary(student_id: str) -> dict:
    """Return a summary of the student's progress across all topics."""
    student = get_or_create_student(student_id)
    topics = []
    for key, score in student.scores.items():
        topics.append(
            {
                "subject": score.subject,
                "topic": score.topic,
                "attempts": score.attempts,
                "correct": score.correct,
                "accuracy": f"{score.accuracy:.0%}",
                "difficulty": score.current_difficulty.value,
                "last_attempt": score.last_attempt.isoformat() if score.last_attempt else None,
            }
        )
    return {
        "student_id": student.student_id,
        "name": student.name,
        "topics": topics,
    }
