from fastapi import APIRouter, HTTPException

from app.agent import build_agent
from app.db.migrations import load_session, save_message
from app.schemas import AgentRequest, AgentResponse
from app.store import get_store

router = APIRouter()


@router.post("/respond", response_model=AgentResponse)
async def respond(payload: AgentRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    store = get_store()

    # 1. Load full conversation history for this session from Postgres
    history = await load_session(payload.session_id)
    history.append({"role": "user", "content": payload.text})

    # 2. Persist the user message immediately
    await save_message(
        session_id=payload.session_id,
        user_id=payload.user_id,
        role="user",
        content=payload.text,
    )

    # 3. Snapshot memory count so we can detect new writes
    before = await store.asearch(
        ("memories", payload.user_id),
        query=payload.text,
        limit=100,
    )

    # 4. Run the agent with full history
    agent = build_agent(user_id=payload.user_id)
    try:
        result = await agent.ainvoke({"messages": history})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    reply = result["messages"][-1].content

    # 5. Persist the assistant reply
    await save_message(
        session_id=payload.session_id,
        user_id=payload.user_id,
        role="assistant",
        content=reply,
    )

    # 6. Detect whether new memories were stored
    after = await store.asearch(
        ("memories", payload.user_id),
        query=payload.text,
        limit=100,
    )
    memories_updated = len(after) > len(before)

    return AgentResponse(
        ok=True,
        result={
            "id": "msg_" + payload.session_id[-6:],
            "text": reply,
            "source": "langgraph",
            "memories_updated": memories_updated,
            "toast": "Memory updated" if memories_updated else None,
        },
    )