from fastapi import APIRouter

from app.db.migrations import delete_session, get_session_messages

router = APIRouter()


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Return the full message history for a session."""
    messages = await get_session_messages(session_id)
    return {"session_id": session_id, "messages": messages, "total": len(messages)}


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """Delete all messages for a session."""
    count = await delete_session(session_id)
    return {"cleared": count, "session_id": session_id}