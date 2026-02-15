"""Conversational chat service using Azure OpenAI."""

import logging

from app.azure_client import get_openai_client
from app.config import get_settings
from app.models import ChatMessage, ChatRequest, ChatResponse, Role
from app.prompts import TUTOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# In-memory session store (swap for Redis / Cosmos DB in production)
_sessions: dict[str, list[ChatMessage]] = {}

MAX_HISTORY = 50  # max messages per session to keep context manageable


async def chat(request: ChatRequest) -> ChatResponse:
    """Send a student message and get a tutor reply."""
    client = get_openai_client()
    settings = get_settings()

    # Retrieve or initialize session history
    history = _sessions.setdefault(request.session_id, [])

    # Build messages payload
    system_content = TUTOR_SYSTEM_PROMPT
    if request.subject:
        system_content += f"\n\nThe student is currently studying: **{request.subject}**."

    messages: list[dict] = [{"role": "system", "content": system_content}]

    # Add conversation history (trimmed to last MAX_HISTORY messages)
    for msg in history[-MAX_HISTORY:]:
        messages.append({"role": msg.role.value, "content": msg.content})

    # Add the new user message
    messages.append({"role": "user", "content": request.message})

    logger.info("Chat session=%s messages=%d", request.session_id, len(messages))

    response = await client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content or ""

    # Persist to session history
    history.append(ChatMessage(role=Role.USER, content=request.message))
    history.append(ChatMessage(role=Role.ASSISTANT, content=reply))

    return ChatResponse(
        session_id=request.session_id,
        reply=reply,
        subject=request.subject,
    )


def get_session_history(session_id: str) -> list[ChatMessage]:
    """Return the conversation history for a session."""
    return _sessions.get(session_id, [])


def clear_session(session_id: str) -> None:
    """Clear a conversation session."""
    _sessions.pop(session_id, None)
