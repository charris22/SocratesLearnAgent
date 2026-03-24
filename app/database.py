"""SQLite persistence layer using aiosqlite."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "socrates.db"

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Return the shared database connection, opening it if needed."""
    global _db
    if _db is None:
        raise RuntimeError("Database not initialised – call init_db() first")
    return _db


async def init_db(db_path: str | Path | None = None) -> None:
    """Create tables and open a persistent connection."""
    global _db
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    _db = await aiosqlite.connect(str(path))
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL")
    await _db.execute("PRAGMA foreign_keys=ON")
    await _create_tables(_db)
    await _db.commit()
    logger.info("Database initialised at %s", path)


async def close_db() -> None:
    """Close the database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None


# ── Schema ───────────────────────────────────────────────────────────────────

async def _create_tables(db: aiosqlite.Connection) -> None:
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            student_id   TEXT PRIMARY KEY,
            name         TEXT NOT NULL DEFAULT 'Student',
            grade        TEXT NOT NULL DEFAULT '',
            interests    TEXT NOT NULL DEFAULT '[]',   -- JSON array
            strengths    TEXT NOT NULL DEFAULT '[]',   -- JSON array
            pacing       TEXT NOT NULL DEFAULT 'standard',
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS topic_scores (
            student_id         TEXT NOT NULL REFERENCES students(student_id),
            subject            TEXT NOT NULL,
            topic              TEXT NOT NULL,
            attempts           INTEGER NOT NULL DEFAULT 0,
            correct            INTEGER NOT NULL DEFAULT 0,
            current_difficulty TEXT NOT NULL DEFAULT 'medium',
            last_attempt       TEXT,
            PRIMARY KEY (student_id, subject, topic)
        );

        CREATE TABLE IF NOT EXISTS concept_mastery (
            student_id     TEXT NOT NULL REFERENCES students(student_id),
            concept        TEXT NOT NULL,
            subject        TEXT NOT NULL DEFAULT '',
            mastery_score  REAL NOT NULL DEFAULT 0.0,
            confidence     REAL NOT NULL DEFAULT 0.0,
            evidence_count INTEGER NOT NULL DEFAULT 0,
            streak         INTEGER NOT NULL DEFAULT 0,
            last_seen      TEXT,
            PRIMARY KEY (student_id, concept)
        );

        CREATE TABLE IF NOT EXISTS learning_events (
            id          TEXT PRIMARY KEY,
            student_id  TEXT NOT NULL REFERENCES students(student_id),
            kind        TEXT NOT NULL,
            subject     TEXT NOT NULL DEFAULT '',
            concept     TEXT NOT NULL DEFAULT '',
            correct     INTEGER,          -- NULL, 0, or 1
            detail      TEXT NOT NULL DEFAULT '',
            timestamp   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            timestamp  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id);

        CREATE TABLE IF NOT EXISTS quiz_questions (
            id              TEXT PRIMARY KEY,
            question        TEXT NOT NULL,
            choices         TEXT NOT NULL,  -- JSON array
            correct_index   INTEGER NOT NULL,
            explanation     TEXT NOT NULL,
            difficulty      TEXT NOT NULL,
            concept         TEXT NOT NULL DEFAULT '',
            cognitive_level TEXT NOT NULL DEFAULT 'application'
        );

        CREATE TABLE IF NOT EXISTS worksheets (
            id         TEXT PRIMARY KEY,
            title      TEXT NOT NULL,
            subject    TEXT NOT NULL,
            topic      TEXT NOT NULL,
            difficulty TEXT NOT NULL DEFAULT 'medium',
            items      TEXT NOT NULL DEFAULT '[]',  -- JSON array
            student_id TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)


# ═════════════════════════════════════════════════════════════════════════════
#  STUDENT CRUD
# ═════════════════════════════════════════════════════════════════════════════

async def upsert_student(
    student_id: str,
    name: str = "Student",
    grade: str = "",
    interests: list[str] | None = None,
    strengths: list[str] | None = None,
    pacing: str = "standard",
) -> dict:
    """Insert or update a student row, returning the full row as dict."""
    db = await get_db()
    await db.execute(
        """INSERT INTO students (student_id, name, grade, interests, strengths, pacing)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(student_id) DO UPDATE SET
             name      = COALESCE(excluded.name, students.name),
             grade     = COALESCE(excluded.grade, students.grade),
             interests = COALESCE(excluded.interests, students.interests),
             strengths = COALESCE(excluded.strengths, students.strengths),
             pacing    = COALESCE(excluded.pacing, students.pacing)
        """,
        (
            student_id,
            name,
            grade,
            json.dumps(interests or []),
            json.dumps(strengths or []),
            pacing,
        ),
    )
    await db.commit()
    return await get_student(student_id)


async def get_student(student_id: str) -> dict | None:
    db = await get_db()
    row = await db.execute_fetchall(
        "SELECT * FROM students WHERE student_id = ?", (student_id,)
    )
    if not row:
        return None
    r = row[0]
    return {
        "student_id": r["student_id"],
        "name": r["name"],
        "grade": r["grade"],
        "interests": json.loads(r["interests"]),
        "strengths": json.loads(r["strengths"]),
        "pacing": r["pacing"],
        "created_at": r["created_at"],
    }


async def ensure_student(student_id: str, name: str = "Student") -> dict:
    """Get existing student or create a new one."""
    existing = await get_student(student_id)
    if existing:
        return existing
    return await upsert_student(student_id, name=name)


# ═════════════════════════════════════════════════════════════════════════════
#  TOPIC SCORES
# ═════════════════════════════════════════════════════════════════════════════

async def get_topic_score(student_id: str, subject: str, topic: str) -> dict:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM topic_scores WHERE student_id=? AND subject=? AND topic=?",
        (student_id, subject, topic),
    )
    if rows:
        r = rows[0]
        return dict(r)
    return {
        "student_id": student_id,
        "subject": subject,
        "topic": topic,
        "attempts": 0,
        "correct": 0,
        "current_difficulty": "medium",
        "last_attempt": None,
    }


async def upsert_topic_score(
    student_id: str, subject: str, topic: str,
    attempts: int, correct: int, current_difficulty: str, last_attempt: str | None,
) -> None:
    db = await get_db()
    await db.execute(
        """INSERT INTO topic_scores
             (student_id, subject, topic, attempts, correct, current_difficulty, last_attempt)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(student_id, subject, topic) DO UPDATE SET
             attempts=excluded.attempts, correct=excluded.correct,
             current_difficulty=excluded.current_difficulty,
             last_attempt=excluded.last_attempt
        """,
        (student_id, subject, topic, attempts, correct, current_difficulty, last_attempt),
    )
    await db.commit()


async def get_all_topic_scores(student_id: str) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM topic_scores WHERE student_id=?", (student_id,)
    )
    return [dict(r) for r in rows]


# ═════════════════════════════════════════════════════════════════════════════
#  CONCEPT MASTERY
# ═════════════════════════════════════════════════════════════════════════════

async def get_concept_mastery(student_id: str, concept: str) -> dict | None:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM concept_mastery WHERE student_id=? AND concept=?",
        (student_id, concept),
    )
    return dict(rows[0]) if rows else None


async def upsert_concept_mastery(
    student_id: str, concept: str, subject: str,
    mastery_score: float, confidence: float, evidence_count: int,
    streak: int, last_seen: str | None,
) -> None:
    db = await get_db()
    await db.execute(
        """INSERT INTO concept_mastery
             (student_id, concept, subject, mastery_score, confidence,
              evidence_count, streak, last_seen)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(student_id, concept) DO UPDATE SET
             subject=excluded.subject, mastery_score=excluded.mastery_score,
             confidence=excluded.confidence, evidence_count=excluded.evidence_count,
             streak=excluded.streak, last_seen=excluded.last_seen
        """,
        (student_id, concept, subject, mastery_score, confidence,
         evidence_count, streak, last_seen),
    )
    await db.commit()


async def get_all_concept_mastery(student_id: str) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM concept_mastery WHERE student_id=?", (student_id,)
    )
    return [dict(r) for r in rows]


async def get_concept_mastery_by_subject(student_id: str, subject: str) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM concept_mastery WHERE student_id=? AND subject=?",
        (student_id, subject),
    )
    return [dict(r) for r in rows]


# ═════════════════════════════════════════════════════════════════════════════
#  LEARNING EVENTS
# ═════════════════════════════════════════════════════════════════════════════

async def insert_event(
    event_id: str, student_id: str, kind: str,
    subject: str = "", concept: str = "",
    correct: bool | None = None, detail: str = "",
) -> None:
    db = await get_db()
    await db.execute(
        """INSERT INTO learning_events
             (id, student_id, kind, subject, concept, correct, detail)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (event_id, student_id, kind, subject, concept,
         None if correct is None else (1 if correct else 0), detail),
    )
    await db.commit()


async def get_recent_events(student_id: str, limit: int = 20) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM learning_events WHERE student_id=? ORDER BY timestamp DESC LIMIT ?",
        (student_id, limit),
    )
    result = []
    for r in rows:
        d = dict(r)
        d["correct"] = None if d["correct"] is None else bool(d["correct"])
        result.append(d)
    return list(reversed(result))  # chronological order


async def count_events(student_id: str) -> int:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT COUNT(*) as cnt FROM learning_events WHERE student_id=?",
        (student_id,),
    )
    return rows[0]["cnt"]


# ═════════════════════════════════════════════════════════════════════════════
#  CHAT MESSAGES
# ═════════════════════════════════════════════════════════════════════════════

async def append_chat_message(session_id: str, role: str, content: str) -> None:
    db = await get_db()
    await db.execute(
        "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content),
    )
    await db.commit()


async def get_chat_history(session_id: str, limit: int = 50) -> list[dict]:
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT role, content, timestamp FROM chat_messages
           WHERE session_id=? ORDER BY id DESC LIMIT ?""",
        (session_id, limit),
    )
    return [dict(r) for r in reversed(rows)]


async def delete_chat_session(session_id: str) -> None:
    db = await get_db()
    await db.execute("DELETE FROM chat_messages WHERE session_id=?", (session_id,))
    await db.commit()


# ═════════════════════════════════════════════════════════════════════════════
#  QUIZ QUESTIONS
# ═════════════════════════════════════════════════════════════════════════════

async def save_quiz_question(q: dict) -> None:
    db = await get_db()
    await db.execute(
        """INSERT OR REPLACE INTO quiz_questions
             (id, question, choices, correct_index, explanation,
              difficulty, concept, cognitive_level)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            q["id"], q["question"], json.dumps(q["choices"]),
            q["correct_index"], q["explanation"], q["difficulty"],
            q.get("concept", ""), q.get("cognitive_level", "application"),
        ),
    )
    await db.commit()


async def get_quiz_question(question_id: str) -> dict | None:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM quiz_questions WHERE id=?", (question_id,)
    )
    if not rows:
        return None
    r = dict(rows[0])
    r["choices"] = json.loads(r["choices"])
    return r


# ═════════════════════════════════════════════════════════════════════════════
#  WORKSHEETS
# ═════════════════════════════════════════════════════════════════════════════

async def save_worksheet(ws: dict) -> None:
    db = await get_db()
    await db.execute(
        """INSERT OR REPLACE INTO worksheets
             (id, title, subject, topic, difficulty, items, student_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            ws["id"], ws["title"], ws["subject"], ws["topic"],
            ws["difficulty"], json.dumps(ws["items"]), ws.get("student_id", ""),
        ),
    )
    await db.commit()


async def get_worksheet_row(worksheet_id: str) -> dict | None:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM worksheets WHERE id=?", (worksheet_id,)
    )
    if not rows:
        return None
    r = dict(rows[0])
    r["items"] = json.loads(r["items"])
    return r


async def list_worksheets(student_id: str) -> list[dict]:
    """Return all worksheets for a student, newest first."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id, title, subject, topic, difficulty, created_at FROM worksheets "
        "WHERE student_id=? ORDER BY created_at DESC",
        (student_id,),
    )
    return [dict(r) for r in rows]
