"""Tests for progress service (offline, no LLM calls)."""

from app.services.progress_service import (
    get_or_create_student,
    record_answer,
    get_student_summary,
    _students,
)


def setup_function():
    """Clear in-memory store before each test."""
    _students.clear()


def test_get_or_create_student_new():
    student = get_or_create_student("test-1", "Owen")
    assert student.student_id == "test-1"
    assert student.name == "Owen"


def test_get_or_create_student_existing():
    get_or_create_student("test-1", "Owen")
    student = get_or_create_student("test-1", "Different Name")
    assert student.name == "Owen"  # keeps original name


def test_record_answer_correct():
    score = record_answer("test-1", "Math", "Fractions", correct=True)
    assert score.attempts == 1
    assert score.correct == 1


def test_record_answer_incorrect():
    score = record_answer("test-1", "Math", "Fractions", correct=False)
    assert score.attempts == 1
    assert score.correct == 0


def test_record_answer_accumulates():
    record_answer("test-1", "Math", "Fractions", correct=True)
    record_answer("test-1", "Math", "Fractions", correct=True)
    score = record_answer("test-1", "Math", "Fractions", correct=False)
    assert score.attempts == 3
    assert score.correct == 2


def test_get_student_summary():
    record_answer("test-1", "Math", "Fractions", correct=True)
    record_answer("test-1", "Science", "Biology", correct=False)
    summary = get_student_summary("test-1")
    assert summary["student_id"] == "test-1"
    assert len(summary["topics"]) == 2
