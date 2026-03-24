"""Pydantic models for the tutoring agent domain."""

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Chat ─────────────────────────────────────────────────────────────────────

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: Role
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    message: str
    subject: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    subject: str | None = None


# ── Quiz ─────────────────────────────────────────────────────────────────────

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CognitiveLevel(str, Enum):
    RECALL = "recall"
    APPLICATION = "application"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"


class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    question: str
    choices: list[str]
    correct_index: int
    explanation: str
    difficulty: Difficulty
    concept: str = ""
    cognitive_level: CognitiveLevel = CognitiveLevel.APPLICATION


class QuizRequest(BaseModel):
    subject: str
    topic: str
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: Difficulty = Difficulty.MEDIUM


class QuizSubmission(BaseModel):
    session_id: str
    question_id: str
    selected_index: int


class QuizResult(BaseModel):
    question_id: str
    correct: bool
    correct_index: int
    explanation: str
    concept: str = ""
    recommendation: str = ""


# ── Progress / Mastery ───────────────────────────────────────────────────────

class TopicScore(BaseModel):
    subject: str
    topic: str
    attempts: int = 0
    correct: int = 0
    current_difficulty: Difficulty = Difficulty.MEDIUM
    last_attempt: datetime | None = None

    @property
    def accuracy(self) -> float:
        return self.correct / self.attempts if self.attempts else 0.0


class ConceptMastery(BaseModel):
    concept: str
    subject: str
    mastery_score: float = 0.0  # 0.0 – 1.0
    confidence: float = 0.0     # 0.0 – 1.0  (rises with evidence count)
    evidence_count: int = 0
    streak: int = 0             # consecutive correct
    last_seen: datetime | None = None

    def record(self, correct: bool) -> None:
        self.evidence_count += 1
        self.last_seen = datetime.now(UTC)
        # Exponential moving average for mastery
        alpha = min(0.4, 2.0 / (self.evidence_count + 1))
        self.mastery_score = (1 - alpha) * self.mastery_score + alpha * (1.0 if correct else 0.0)
        # Confidence grows with evidence
        self.confidence = min(1.0, self.evidence_count / 10.0)
        self.streak = (self.streak + 1) if correct else 0


class LearnerPacing(str, Enum):
    STANDARD = "standard"
    ACCELERATED = "accelerated"
    ENRICHED = "enriched"  # depth over speed


class LearningEventKind(str, Enum):
    CHAT = "chat"
    QUIZ = "quiz"
    WORKSHEET = "worksheet"
    HINT_USED = "hint_used"
    REFLECTION = "reflection"


class LearningEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    student_id: str
    kind: LearningEventKind
    subject: str = ""
    concept: str = ""
    correct: bool | None = None
    detail: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StudentProfile(BaseModel):
    student_id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = "Student"
    grade: str = ""
    interests: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    pacing: LearnerPacing = LearnerPacing.STANDARD
    scores: dict[str, TopicScore] = Field(default_factory=dict)     # key = "subject::topic"
    mastery: dict[str, ConceptMastery] = Field(default_factory=dict) # key = concept
    events: list[LearningEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def topic_key(self, subject: str, topic: str) -> str:
        return f"{subject}::{topic}"

    def get_score(self, subject: str, topic: str) -> TopicScore:
        key = self.topic_key(subject, topic)
        if key not in self.scores:
            self.scores[key] = TopicScore(subject=subject, topic=topic)
        return self.scores[key]

    def get_mastery(self, concept: str, subject: str = "") -> ConceptMastery:
        if concept not in self.mastery:
            self.mastery[concept] = ConceptMastery(concept=concept, subject=subject)
        return self.mastery[concept]

    def add_event(self, event: LearningEvent) -> None:
        self.events.append(event)

    @property
    def mastery_summary(self) -> dict[str, float]:
        return {k: v.mastery_score for k, v in self.mastery.items()}


# ── Recommendations ──────────────────────────────────────────────────────────

class Recommendation(BaseModel):
    concept: str
    subject: str
    reason: str
    suggested_difficulty: Difficulty
    suggested_activity: str  # "quiz", "chat_lesson", "worksheet", "review"


# ── Worksheets ───────────────────────────────────────────────────────────────

class WorksheetItem(BaseModel):
    number: int
    question: str
    answer_key: str = ""
    concept: str = ""
    difficulty: Difficulty = Difficulty.MEDIUM
    points: int = 1


class Worksheet(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    title: str
    subject: str
    topic: str
    difficulty: Difficulty = Difficulty.MEDIUM
    items: list[WorksheetItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    student_id: str = ""

    @property
    def total_points(self) -> int:
        return sum(item.points for item in self.items)


class WorksheetRequest(BaseModel):
    subject: str
    topic: str
    num_items: int = Field(default=10, ge=1, le=30)
    difficulty: Difficulty = Difficulty.MEDIUM
    student_id: str = "default"
    include_answer_key: bool = True


class AnswerEntry(BaseModel):
    number: int
    student_answer: str


class WorksheetSubmission(BaseModel):
    worksheet_id: str
    student_id: str = "default"
    answers: list[AnswerEntry]


class ScoredItem(BaseModel):
    number: int
    correct: bool
    student_answer: str
    correct_answer: str
    feedback: str = ""
    concept: str = ""


class WorksheetResult(BaseModel):
    worksheet_id: str
    total: int
    earned: int
    percentage: float
    items: list[ScoredItem]
    recommendations: list[str] = Field(default_factory=list)


# ── Profile API models ───────────────────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    grade: str | None = None
    interests: list[str] | None = None
    strengths: list[str] | None = None
    pacing: LearnerPacing | None = None
