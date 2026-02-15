"""Unit tests for models."""

from app.models import Difficulty, StudentProfile, TopicScore


def test_topic_score_accuracy_zero_attempts():
    score = TopicScore(subject="Math", topic="Fractions")
    assert score.accuracy == 0.0


def test_topic_score_accuracy():
    score = TopicScore(subject="Math", topic="Fractions", attempts=10, correct=7)
    assert score.accuracy == 0.7


def test_student_profile_get_score_creates():
    student = StudentProfile(name="Owen")
    score = student.get_score("Math", "Algebra")
    assert score.subject == "Math"
    assert score.topic == "Algebra"
    assert score.attempts == 0


def test_student_profile_get_score_returns_existing():
    student = StudentProfile(name="Owen")
    score1 = student.get_score("Math", "Algebra")
    score1.attempts = 5
    score2 = student.get_score("Math", "Algebra")
    assert score2.attempts == 5


def test_difficulty_enum():
    assert Difficulty.EASY.value == "easy"
    assert Difficulty.MEDIUM.value == "medium"
    assert Difficulty.HARD.value == "hard"
