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


class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    question: str
    choices: list[str]
    correct_index: int
    explanation: str
    difficulty: Difficulty


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


# ── Progress ─────────────────────────────────────────────────────────────────

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


class StudentProfile(BaseModel):
    student_id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = "Student"
    scores: dict[str, TopicScore] = Field(default_factory=dict)  # key = "subject::topic"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def topic_key(self, subject: str, topic: str) -> str:
        return f"{subject}::{topic}"

    def get_score(self, subject: str, topic: str) -> TopicScore:
        key = self.topic_key(subject, topic)
        if key not in self.scores:
            self.scores[key] = TopicScore(subject=subject, topic=topic)
        return self.scores[key]
