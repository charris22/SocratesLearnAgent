"""Chat API endpoints."""

from fastapi import APIRouter, HTTPException

from app.models import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to the tutor and get a response."""
    try:
        return await chat_service.chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/history")
async def get_history(session_id: str):
    """Get the conversation history for a session."""
    history = chat_service.get_session_history(session_id)
    return {"session_id": session_id, "messages": [m.model_dump() for m in history]}


@router.delete("/{session_id}")
async def clear_chat(session_id: str):
    """Clear a conversation session."""
    chat_service.clear_session(session_id)
    return {"ok": True}
