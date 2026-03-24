"""Tests for progress service (offline, no LLM calls)."""

import pytest

from app import database as db
from app.models import Difficulty, LearnerPacing, LearningEventKind, ProfileUpdateRequest
from app.services.progress_service import (
    _students,
    get_adaptation_instructions,
    get_or_create_student,
    get_profile,
    get_student_summary,
    record_answer,
    record_concept,
    record_event,
    suggest_difficulty,
    update_profile,
)
from app.prompts import ADAPTATION_GIFTED_READY, ADAPTATION_ON_TRACK, ADAPTATION_STRUGGLING


@pytest.fixture(autouse=True)
async def _fresh_db():
    """Spin up an in-memory SQLite DB and clear the cache before each test."""
    await db.init_db(":memory:")
    _students.clear()
    yield
    await db.close_db()


# ── get_or_create_student ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_or_create_student_new():
    student = await get_or_create_student("test-1", "Owen")
    assert student.student_id == "test-1"
    assert student.name == "Owen"


@pytest.mark.asyncio
async def test_get_or_create_student_existing():
    await get_or_create_student("test-1", "Owen")
    student = await get_or_create_student("test-1", "Different Name")
    assert student.name == "Owen"  # keeps original name


# ── record_answer ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_record_answer_correct():
    score = await record_answer("test-1", "Math", "Fractions", correct=True)
    assert score.attempts == 1
    assert score.correct == 1


@pytest.mark.asyncio
async def test_record_answer_incorrect():
    score = await record_answer("test-1", "Math", "Fractions", correct=False)
    assert score.attempts == 1
    assert score.correct == 0


@pytest.mark.asyncio
async def test_record_answer_accumulates():
    await record_answer("test-1", "Math", "Fractions", correct=True)
    await record_answer("test-1", "Math", "Fractions", correct=True)
    score = await record_answer("test-1", "Math", "Fractions", correct=False)
    assert score.attempts == 3
    assert score.correct == 2


# ── record_concept ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_record_concept_updates_mastery():
    m = await record_concept("test-1", "fractions", "Math", correct=True)
    assert m.evidence_count == 1
    assert m.mastery_score > 0.0
    assert m.streak == 1


@pytest.mark.asyncio
async def test_record_concept_accumulates():
    await record_concept("test-1", "fractions", "Math", correct=True)
    await record_concept("test-1", "fractions", "Math", correct=True)
    m = await record_concept("test-1", "fractions", "Math", correct=False)
    assert m.evidence_count == 3
    assert m.streak == 0


# ── record_event ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_record_event_appends():
    event = await record_event("test-1", LearningEventKind.QUIZ, subject="Math", concept="fractions")
    student = await get_or_create_student("test-1")
    assert len(student.events) == 1
    assert student.events[0].id == event.id
    assert event.kind == LearningEventKind.QUIZ


# ── update_profile ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_profile_partial():
    await get_or_create_student("test-1", "Owen")
    req = ProfileUpdateRequest(grade="7th", interests=["robotics", "space"])
    updated = await update_profile("test-1", req)
    assert updated.grade == "7th"
    assert updated.interests == ["robotics", "space"]
    assert updated.name == "Owen"  # unchanged


@pytest.mark.asyncio
async def test_update_profile_pacing():
    await get_or_create_student("test-1", "Owen")
    req = ProfileUpdateRequest(pacing=LearnerPacing.ENRICHED)
    updated = await update_profile("test-1", req)
    assert updated.pacing == LearnerPacing.ENRICHED


# ── get_profile ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_profile():
    await get_or_create_student("test-1", "Owen")
    profile = await get_profile("test-1")
    assert profile["name"] == "Owen"
    assert profile["student_id"] == "test-1"
    assert "pacing" in profile


# ── get_adaptation_instructions ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_adaptation_no_data_returns_on_track():
    await get_or_create_student("test-1")
    result = await get_adaptation_instructions("test-1", "Math")
    assert result == ADAPTATION_ON_TRACK


@pytest.mark.asyncio
async def test_adaptation_struggling():
    await get_or_create_student("test-1")
    # Record enough low-mastery data
    for _ in range(5):
        await record_concept("test-1", "fractions", "Math", correct=False)
    result = await get_adaptation_instructions("test-1", "Math")
    assert result == ADAPTATION_STRUGGLING


@pytest.mark.asyncio
async def test_adaptation_gifted_ready():
    await get_or_create_student("test-1")
    for _ in range(10):
        await record_concept("test-1", "fractions", "Math", correct=True)
    result = await get_adaptation_instructions("test-1", "Math")
    assert result == ADAPTATION_GIFTED_READY


@pytest.mark.asyncio
async def test_adaptation_enriched_pacing_always_gifted():
    student = await get_or_create_student("test-1")
    student.pacing = LearnerPacing.ENRICHED
    # Record some moderate data
    for _ in range(3):
        await record_concept("test-1", "fractions", "Math", correct=True)
        await record_concept("test-1", "fractions", "Math", correct=False)
    result = await get_adaptation_instructions("test-1", "Math")
    assert result == ADAPTATION_GIFTED_READY


# ── suggest_difficulty ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_suggest_difficulty_insufficient_data():
    await get_or_create_student("test-1")
    result = await suggest_difficulty("test-1", "Math", "Fractions")
    assert result == Difficulty.MEDIUM  # default


@pytest.mark.asyncio
async def test_suggest_difficulty_upgrade_on_high_accuracy():
    for _ in range(5):
        await record_answer("test-1", "Math", "Fractions", correct=True)
    result = await suggest_difficulty("test-1", "Math", "Fractions")
    assert result == Difficulty.HARD


@pytest.mark.asyncio
async def test_suggest_difficulty_downgrade_on_low_accuracy():
    for _ in range(5):
        await record_answer("test-1", "Math", "Fractions", correct=False)
    result = await suggest_difficulty("test-1", "Math", "Fractions")
    assert result == Difficulty.EASY


# ── get_student_summary ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_student_summary():
    await record_answer("test-1", "Math", "Fractions", correct=True)
    await record_answer("test-1", "Science", "Biology", correct=False)
    await record_concept("test-1", "fractions", "Math", correct=True)
    summary = await get_student_summary("test-1")
    assert summary["student_id"] == "test-1"
    assert len(summary["topics"]) == 2
    assert len(summary["mastery"]) == 1
    assert "event_count" in summary
