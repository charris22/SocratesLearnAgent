"""Unit tests for models."""

from app.models import (
    CognitiveLevel,
    ConceptMastery,
    Difficulty,
    LearnerPacing,
    LearningEvent,
    LearningEventKind,
    StudentProfile,
    TopicScore,
    Worksheet,
    WorksheetItem,
)


# ── TopicScore ────────────────────────────────────────────────────────────────

def test_topic_score_accuracy_zero_attempts():
    score = TopicScore(subject="Math", topic="Fractions")
    assert score.accuracy == 0.0


def test_topic_score_accuracy():
    score = TopicScore(subject="Math", topic="Fractions", attempts=10, correct=7)
    assert score.accuracy == 0.7


# ── Enums ─────────────────────────────────────────────────────────────────────

def test_difficulty_enum():
    assert Difficulty.EASY.value == "easy"
    assert Difficulty.MEDIUM.value == "medium"
    assert Difficulty.HARD.value == "hard"


def test_cognitive_level_enum():
    assert CognitiveLevel.RECALL.value == "recall"
    assert CognitiveLevel.SYNTHESIS.value == "synthesis"


def test_learner_pacing_enum():
    assert LearnerPacing.STANDARD.value == "standard"
    assert LearnerPacing.ENRICHED.value == "enriched"


# ── ConceptMastery ────────────────────────────────────────────────────────────

def test_concept_mastery_record_correct():
    m = ConceptMastery(concept="fractions", subject="Math")
    m.record(True)
    assert m.evidence_count == 1
    assert m.mastery_score > 0.0
    assert m.streak == 1
    assert m.confidence > 0.0
    assert m.last_seen is not None


def test_concept_mastery_record_incorrect_resets_streak():
    m = ConceptMastery(concept="fractions", subject="Math")
    m.record(True)
    m.record(True)
    assert m.streak == 2
    m.record(False)
    assert m.streak == 0


def test_concept_mastery_ema_converges():
    m = ConceptMastery(concept="fractions", subject="Math")
    for _ in range(20):
        m.record(True)
    assert m.mastery_score > 0.9
    assert m.confidence == 1.0


def test_concept_mastery_mixed_results():
    m = ConceptMastery(concept="fractions", subject="Math")
    for _ in range(5):
        m.record(True)
    for _ in range(5):
        m.record(False)
    # Mastery should drop below 1.0 after misses
    assert m.mastery_score < 0.8


# ── StudentProfile ────────────────────────────────────────────────────────────

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


def test_student_profile_get_mastery_creates():
    student = StudentProfile(name="Owen")
    m = student.get_mastery("fractions", "Math")
    assert m.concept == "fractions"
    assert m.subject == "Math"
    assert m.evidence_count == 0


def test_student_profile_get_mastery_returns_existing():
    student = StudentProfile(name="Owen")
    m1 = student.get_mastery("fractions", "Math")
    m1.record(True)
    m2 = student.get_mastery("fractions")
    assert m2.evidence_count == 1


def test_student_profile_add_event():
    student = StudentProfile(name="Owen")
    event = LearningEvent(
        student_id=student.student_id,
        kind=LearningEventKind.QUIZ,
        subject="Math",
        concept="fractions",
        correct=True,
    )
    student.add_event(event)
    assert len(student.events) == 1
    assert student.events[0].kind == LearningEventKind.QUIZ


def test_student_profile_mastery_summary():
    student = StudentProfile(name="Owen")
    m = student.get_mastery("fractions", "Math")
    m.record(True)
    m.record(True)
    summary = student.mastery_summary
    assert "fractions" in summary
    assert summary["fractions"] > 0.0


# ── Worksheet ─────────────────────────────────────────────────────────────────

def test_worksheet_total_points():
    ws = Worksheet(
        title="Test",
        subject="Math",
        topic="Fractions",
        items=[
            WorksheetItem(number=1, question="Q1", points=2),
            WorksheetItem(number=2, question="Q2", points=3),
            WorksheetItem(number=3, question="Q3", points=1),
        ],
    )
    assert ws.total_points == 6


def test_worksheet_empty_points():
    ws = Worksheet(title="Empty", subject="Math", topic="Algebra", items=[])
    assert ws.total_points == 0
