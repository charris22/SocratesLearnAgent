"""Conversational chat service using Azure OpenAI."""

import logging

from app.azure_client import get_openai_client
from app import database as db
from app.config import get_settings
from app.models import ChatMessage, ChatRequest, ChatResponse, LearningEventKind, Role
from app.prompts import ADAPTIVE_CONTEXT_TEMPLATE, TUTOR_SYSTEM_PROMPT
from app.services import progress_service

logger = logging.getLogger(__name__)

MAX_HISTORY = 50  # max messages per session to keep context manageable


async def _build_system_prompt(request: ChatRequest) -> str:
    """Build adaptive system prompt using student profile + mastery."""
    base = TUTOR_SYSTEM_PROMPT

    if request.subject:
        base += (
            f"\n\nThe student is currently studying: **{request.subject}**."
            f" You MUST keep ALL responses focused on {request.subject}."
            f" If the student asks about anything outside {request.subject},"
            f" do NOT answer it — redirect them back to {request.subject} immediately."
        )

    # Try to inject learner context
    student_id = getattr(request, "student_id", None) or "default"
    student = await progress_service.get_or_create_student(student_id)

    # Mastery summary for relevant concepts
    mastery_lines = []
    for concept, m in student.mastery.items():
        if m.subject == request.subject or not request.subject:
            mastery_lines.append(
                f"  {concept}: mastery={m.mastery_score:.0%}, "
                f"confidence={m.confidence:.0%}, streak={m.streak}"
            )
    mastery_text = "\n".join(mastery_lines) if mastery_lines else "  No mastery data yet."

    adaptation = await progress_service.get_adaptation_instructions(
        student_id, request.subject or ""
    )

    adaptive_block = ADAPTIVE_CONTEXT_TEMPLATE.format(
        name=student.name,
        grade=student.grade or "unknown",
        pacing=student.pacing.value,
        interests=", ".join(student.interests) or "not specified",
        strengths=", ".join(student.strengths) or "not specified",
        mastery_summary=mastery_text,
        adaptation_instructions=adaptation,
    )

    return base + adaptive_block


async def chat(request: ChatRequest) -> ChatResponse:
    """Send a student message and get a tutor reply."""
    client = get_openai_client()
    settings = get_settings()

    # Load history from DB
    history_rows = await db.get_chat_history(request.session_id, limit=MAX_HISTORY)

    system_content = await _build_system_prompt(request)

    messages: list[dict] = [{"role": "system", "content": system_content}]

    for row in history_rows:
        messages.append({"role": row["role"], "content": row["content"]})

    messages.append({"role": "user", "content": request.message})

    logger.info("Chat session=%s messages=%d", request.session_id, len(messages))

    response = await client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content or ""

    # Persist both messages
    await db.append_chat_message(request.session_id, "user", request.message)
    await db.append_chat_message(request.session_id, "assistant", reply)

    # Record as learning event
    student_id = getattr(request, "student_id", None) or "default"
    await progress_service.record_event(
        student_id=student_id,
        kind=LearningEventKind.CHAT,
        subject=request.subject or "",
        detail=request.message[:200],
    )

    return ChatResponse(
        session_id=request.session_id,
        reply=reply,
        subject=request.subject,
    )


async def get_session_history(session_id: str) -> list[ChatMessage]:
    """Return the conversation history for a session."""
    rows = await db.get_chat_history(session_id)
    return [
        ChatMessage(role=Role(r["role"]), content=r["content"], timestamp=r["timestamp"])
        for r in rows
    ]


async def delete_session(session_id: str) -> None:
    """Delete a chat session."""
    await db.delete_chat_session(session_id)


def clear_session(session_id: str) -> None:
    """Clear a conversation session."""
    _sessions.pop(session_id, None)
