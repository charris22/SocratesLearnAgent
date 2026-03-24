"""Student progress tracking, adaptive difficulty, and recommendations."""

import json
import logging
from datetime import UTC, datetime

from app.azure_client import get_openai_client
from app.config import get_settings
from app import database as db
from app.models import (
    ConceptMastery,
    Difficulty,
    LearnerPacing,
    LearningEvent,
    LearningEventKind,
    ProfileUpdateRequest,
    Recommendation,
    StudentProfile,
    TopicScore,
)
from app.prompts import (
    ADAPTATION_GIFTED_READY,
    ADAPTATION_ON_TRACK,
    ADAPTATION_STRUGGLING,
    DIFFICULTY_ASSESSMENT_PROMPT,
    RECOMMENDATION_PROMPT,
)

logger = logging.getLogger(__name__)

# Write-through cache so adaptation logic can work on objects directly.
# Authoritative data lives in SQLite; this is populated on first access.
_students: dict[str, StudentProfile] = {}

# ── Helpers ──────────────────────────────────────────────────────────────────

TARGET_ACCURACY_LOW = 0.55
TARGET_ACCURACY_HIGH = 0.85


async def get_or_create_student(student_id: str, name: str = "Student") -> StudentProfile:
    """Retrieve an existing student profile or create a new one."""
    if student_id in _students:
        return _students[student_id]

    row = await db.get_student(student_id)
    if row:
        profile = StudentProfile(
            student_id=row["student_id"],
            name=row["name"],
            grade=row["grade"],
            interests=row["interests"],
            strengths=row["strengths"],
            pacing=LearnerPacing(row["pacing"]),
        )
        # Hydrate mastery from DB
        mastery_rows = await db.get_all_concept_mastery(student_id)
        for m in mastery_rows:
            profile.mastery[m["concept"]] = ConceptMastery(
                concept=m["concept"],
                subject=m["subject"],
                mastery_score=m["mastery_score"],
                confidence=m["confidence"],
                evidence_count=m["evidence_count"],
                streak=m["streak"],
                last_seen=m["last_seen"],
            )
        # Hydrate topic scores
        score_rows = await db.get_all_topic_scores(student_id)
        for s in score_rows:
            key = f"{s['subject']}::{s['topic']}"
            profile.scores[key] = TopicScore(
                subject=s["subject"],
                topic=s["topic"],
                attempts=s["attempts"],
                correct=s["correct"],
                current_difficulty=Difficulty(s["current_difficulty"]),
                last_attempt=s["last_attempt"],
            )
    else:
        profile = StudentProfile(student_id=student_id, name=name)
        await db.upsert_student(student_id, name=name)

    _students[student_id] = profile
    return profile


async def update_profile(student_id: str, update: ProfileUpdateRequest) -> StudentProfile:
    """Update editable fields on a student profile."""
    student = await get_or_create_student(student_id)
    if update.name is not None:
        student.name = update.name
    if update.grade is not None:
        student.grade = update.grade
    if update.interests is not None:
        student.interests = update.interests
    if update.strengths is not None:
        student.strengths = update.strengths
    if update.pacing is not None:
        student.pacing = update.pacing

    await db.upsert_student(
        student_id,
        name=student.name,
        grade=student.grade,
        interests=student.interests,
        strengths=student.strengths,
        pacing=student.pacing.value,
    )
    return student


# ── Recording ────────────────────────────────────────────────────────────────

async def record_answer(student_id: str, subject: str, topic: str, correct: bool) -> TopicScore:
    """Record a quiz answer and update the student's topic score."""
    student = await get_or_create_student(student_id)
    score = student.get_score(subject, topic)
    score.attempts += 1
    if correct:
        score.correct += 1
    score.last_attempt = datetime.now(UTC)

    await db.upsert_topic_score(
        student_id, subject, topic,
        score.attempts, score.correct, score.current_difficulty.value,
        score.last_attempt.isoformat() if score.last_attempt else None,
    )
    return score


async def record_concept(
    student_id: str, concept: str, subject: str, correct: bool
) -> ConceptMastery:
    """Record a concept-level result and update mastery."""
    student = await get_or_create_student(student_id)
    m = student.get_mastery(concept, subject)
    m.record(correct)

    await db.upsert_concept_mastery(
        student_id, concept, subject,
        m.mastery_score, m.confidence, m.evidence_count, m.streak,
        m.last_seen.isoformat() if m.last_seen else None,
    )
    return m


async def record_event(
    student_id: str,
    kind: LearningEventKind,
    subject: str = "",
    concept: str = "",
    correct: bool | None = None,
    detail: str = "",
) -> LearningEvent:
    """Append a learning event to the student's history."""
    student = await get_or_create_student(student_id)
    event = LearningEvent(
        student_id=student_id,
        kind=kind,
        subject=subject,
        concept=concept,
        correct=correct,
        detail=detail,
    )
    student.add_event(event)

    await db.insert_event(
        event.id, student_id, kind.value, subject, concept, correct, detail,
    )
    return event


# ── Adaptive policies ────────────────────────────────────────────────────────

async def get_adaptation_instructions(student_id: str, subject: str) -> str:
    """Return the right adaptation prompt based on recent performance."""
    student = await get_or_create_student(student_id)

    # Gather mastery scores for concepts in this subject
    relevant = [
        m for m in student.mastery.values()
        if m.subject == subject and m.evidence_count >= 2
    ]
    if not relevant:
        return ADAPTATION_ON_TRACK

    avg_mastery = sum(m.mastery_score for m in relevant) / len(relevant)

    if student.pacing == LearnerPacing.ACCELERATED and avg_mastery > 0.7:
        return ADAPTATION_GIFTED_READY
    if student.pacing == LearnerPacing.ENRICHED:
        return ADAPTATION_GIFTED_READY
    if avg_mastery < TARGET_ACCURACY_LOW:
        return ADAPTATION_STRUGGLING
    if avg_mastery > TARGET_ACCURACY_HIGH:
        return ADAPTATION_GIFTED_READY
    return ADAPTATION_ON_TRACK


async def suggest_difficulty(student_id: str, subject: str, topic: str) -> Difficulty:
    """Quick rule-based difficulty suggestion (no LLM call)."""
    student = await get_or_create_student(student_id)
    score = student.get_score(subject, topic)

    if score.attempts < 3:
        return score.current_difficulty

    acc = score.accuracy
    if acc > TARGET_ACCURACY_HIGH and score.current_difficulty != Difficulty.HARD:
        level = {"easy": Difficulty.MEDIUM, "medium": Difficulty.HARD}
        return level.get(score.current_difficulty.value, Difficulty.HARD)
    if acc < TARGET_ACCURACY_LOW and score.current_difficulty != Difficulty.EASY:
        level = {"hard": Difficulty.MEDIUM, "medium": Difficulty.EASY}
        return level.get(score.current_difficulty.value, Difficulty.EASY)
    return score.current_difficulty


async def recommend_difficulty(
    student_id: str, subject: str, topic: str
) -> tuple[Difficulty, str]:
    """Use the LLM to recommend the next difficulty level based on performance."""
    student = await get_or_create_student(student_id)
    score = student.get_score(subject, topic)

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

    score.current_difficulty = new_difficulty
    await db.upsert_topic_score(
        student_id, subject, topic,
        score.attempts, score.correct, new_difficulty.value,
        score.last_attempt.isoformat() if score.last_attempt else None,
    )
    logger.info(
        "Difficulty for %s/%s -> %s (%s)", subject, topic, new_difficulty.value, reason
    )
    return new_difficulty, reason


# ── Recommendations ──────────────────────────────────────────────────────────

async def get_recommendations(student_id: str) -> list[Recommendation]:
    """Use the LLM to suggest next-best learning activities."""
    student = await get_or_create_student(student_id)

    mastery_data = {
        k: {"mastery": round(v.mastery_score, 2), "evidence": v.evidence_count, "streak": v.streak}
        for k, v in student.mastery.items()
    }

    recent_rows = await db.get_recent_events(student_id, limit=20)
    events_text = "\n".join(
        f"- {e['kind']}: {e['subject']}/{e['concept']} correct={e['correct']}"
        for e in recent_rows
    ) if recent_rows else "No recent activity."

    client = get_openai_client()
    settings = get_settings()

    prompt = RECOMMENDATION_PROMPT.format(
        name=student.name,
        grade=student.grade or "unknown",
        pacing=student.pacing.value,
        interests=", ".join(student.interests) or "not specified",
        strengths=", ".join(student.strengths) or "not specified",
        mastery_json=json.dumps(mastery_data, indent=2),
        recent_events=events_text,
    )

    response = await client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=512,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    data = json.loads(raw)

    recs: list[Recommendation] = []
    for item in data.get("recommendations", []):
        recs.append(Recommendation(
            concept=item.get("concept", ""),
            subject=item.get("subject", ""),
            reason=item.get("reason", ""),
            suggested_difficulty=Difficulty(item.get("suggested_difficulty", "medium")),
            suggested_activity=item.get("suggested_activity", "quiz"),
        ))
    return recs


# ── Summaries ────────────────────────────────────────────────────────────────

async def get_student_summary(student_id: str) -> dict:
    """Return a summary of the student's progress across all topics."""
    student = await get_or_create_student(student_id)

    score_rows = await db.get_all_topic_scores(student_id)
    topics = []
    for s in score_rows:
        attempts = s["attempts"]
        correct = s["correct"]
        accuracy = correct / attempts if attempts else 0.0
        topics.append({
            "subject": s["subject"],
            "topic": s["topic"],
            "attempts": attempts,
            "correct": correct,
            "accuracy": f"{accuracy:.0%}",
            "difficulty": s["current_difficulty"],
            "last_attempt": s["last_attempt"],
        })

    mastery_rows = await db.get_all_concept_mastery(student_id)
    mastery_list = []
    for m in mastery_rows:
        mastery_list.append({
            "concept": m["concept"],
            "subject": m["subject"],
            "mastery_score": round(m["mastery_score"], 2),
            "confidence": round(m["confidence"], 2),
            "evidence_count": m["evidence_count"],
            "streak": m["streak"],
        })

    event_count = await db.count_events(student_id)

    return {
        "student_id": student.student_id,
        "name": student.name,
        "grade": student.grade,
        "pacing": student.pacing.value,
        "interests": student.interests,
        "strengths": student.strengths,
        "topics": topics,
        "mastery": mastery_list,
        "event_count": event_count,
    }


async def get_profile(student_id: str) -> dict:
    """Return the student profile for editing."""
    student = await get_or_create_student(student_id)
    return {
        "student_id": student.student_id,
        "name": student.name,
        "grade": student.grade,
        "interests": student.interests,
        "strengths": student.strengths,
        "pacing": student.pacing.value,
    }
