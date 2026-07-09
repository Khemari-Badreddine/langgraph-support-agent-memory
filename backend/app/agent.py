from services.graph import graph
from services.state import AgentState


async def run_agent(user_id: str, session_id: str, history: list[dict]) -> dict:
    """
    Invoke the multi-agent graph and return a structured result.
    """
    
    initial_state: AgentState = {
        "messages": history,
        "user_id": user_id,
        "session_id": session_id,
        "intent": "",
        "specialist": "",
        "trace": [],
    }

    result: AgentState = await graph.ainvoke(initial_state)

    # The last message in state is the assistant reply
    reply = result["messages"][-1]["content"]

    memories_updated = any(
        step.get("memories_updated") for step in result.get("trace", [])
    )

    return {
        "reply": reply,
        "intent": result["intent"],
        "specialist": result["specialist"],
        "trace": result["trace"],
        "memories_updated": memories_updated,
    }
