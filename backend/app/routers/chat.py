from fastapi import APIRouter
from app.agent import build_agent
from app.schemas import AgentRequest, AgentResponse

router = APIRouter()


@router.post("/respond", response_model=AgentResponse)
async def respond(payload: AgentRequest):
    agent = build_agent(user_id=payload.user_id)

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": payload.text}]}
    )

    reply = result["messages"][-1].content

    return AgentResponse(
        ok=True,
        result={"id": "msg_123", "text": reply, "source": "langgraph", "toast": None},
    )
