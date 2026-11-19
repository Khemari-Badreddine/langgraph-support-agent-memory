from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.agent import run_agent
from app.db.migrations import load_session, save_message
from app.schemas import AgentRequest, AgentResponse, AgentResult, TraceStep

router = APIRouter()


@router.post("/respond", response_model=AgentResponse)
async def respond(payload: AgentRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if not payload.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required.")
    if not payload.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required.")

    # 1. Load conversation history for this session from Postgres
    history = await load_session(payload.session_id)
    history.append({"role": "user", "content": payload.text})

    # 2. Persist user message immediately (also creates the session row)
    try:
        await save_message(
            session_id=payload.session_id,
            user_id=payload.user_id,
            role="user",
            content=payload.text,
        )
    except PermissionError:
        raise HTTPException(
            status_code=403, detail="Session belongs to a different user."
        )

    # 3. Run the multi-agent graph
    try:
        output = await run_agent(
            user_id=payload.user_id,
            session_id=payload.session_id,
            history=history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # 4. Persist assistant reply
    await save_message(
        session_id=payload.session_id,
        user_id=payload.user_id,
        role="assistant",
        content=output["reply"],
    )

    # 5. Build response
    trace_steps = [
        TraceStep(
            step=t["step"],
            detail=t["detail"],
            memories_updated=t.get("memories_updated", False),
        )
        for t in output["trace"]
    ]


    return AgentResponse(
        ok=True,
        result=AgentResult(
            id=f"msg_{uuid4().hex[:8]}",
            text=output["reply"],
            intent=output["intent"],
            specialist=output["specialist"],
            trace=trace_steps,
            memories_updated=output["memories_updated"],

        ),
    )