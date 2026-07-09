from typing import Literal
from uuid import uuid4

from langgraph.graph import END, StateGraph

from services.state import AgentState
from services.helper import make_llm, _run_specialist

from app.prompts import (
    BILLING_PROMPT,
    GENERAL_PROMPT,
    ORDER_PROMPT,
    TECH_PROMPT,
    TRIAGE_PROMPT,
)

from app.store import get_store


# ── Node: Memory ────────────────────────────────────────────────────────────
async def memory_node(state: AgentState) -> AgentState:
    """
    Runs after every specialist. Extracts and stores facts unconditionally.
    The LLM doesn't decide whether to save — the harness does.
    """
    llm = make_llm()
    last_user_msg = next(m for m in reversed(state["messages"]) if m["role"] == "user")
    last_agent_msg = next(
        m for m in reversed(state["messages"]) if m["role"] == "assistant"
    )

    extraction = await llm.ainvoke(
        [
            {
                "role": "system",
                "content": """
            Extract factual, reusable information from this exchange.
            Return a JSON list of strings, each a single fact.
            Example: ["User reported double charge on invoice #INV-123", "User prefers email contact"]
            If nothing worth storing, return [].
            Return ONLY the JSON list, nothing else.
        """,
            },
            {
                "role": "user",
                "content": f"""
            Customer said: {last_user_msg['content']}
            Agent replied: {last_agent_msg['content']}
        """,
            },
        ]
    )

    import json

    try:
        facts = json.loads(extraction.content.strip())
    except Exception:
        facts = []

    for fact in facts:
        await get_store.aput(
            ("memories", state["user_id"]),
            key=str(uuid4()),
            value={"text": fact, "intent": state["intent"]},
        )

    trace = state.get("trace", [])
    if facts:
        trace.append(
            {
                "step": "memory",
                "detail": f"Stored {len(facts)} fact(s): {facts}",
                "memories_updated": True,
            }
        )

    return {**state, "trace": trace}


# ── Node: Triage ────────────────────────────────────────────────────────────
async def triage_node(state: AgentState) -> AgentState:
    """
    Classifies the customer's latest message into an intent.
    Uses a cheap, fast LLM call
    no memory tools needed here.
    """
    llm = make_llm()
    last_message = state["messages"][-1]["content"]

    response = await llm.ainvoke(
        [
            {"role": "system", "content": TRIAGE_PROMPT},
            {"role": "user", "content": last_message},
        ]
    )

    raw = response.content.strip().lower()

    # Defensive: if the model returns something unexpected, fall back to general
    intent = raw if raw in ("billing", "tech", "order", "general") else "general"

    specialist_map = {
        "billing": "Billing Agent",
        "tech": "Tech Support Agent",
        "order": "Order Tracking Agent",
        "general": "General Agent",
    }

    trace = state.get("trace", [])
    trace.append(
        {
            "step": "triage",
            "detail": f"Intent classified as '{intent}' (raw: '{raw}')",
        }
    )

    return {
        **state,
        "intent": intent,
        "specialist": specialist_map[intent],
        "trace": trace,
    }


# ── Router: decides which node runs after triage ──────────────────────────────
def route_intent(state: AgentState) -> Literal["billing", "tech", "order", "general"]:
    return state["intent"]


async def general_node(state: AgentState) -> AgentState:
    return await _run_specialist(state, GENERAL_PROMPT, "general")


async def billing_node(state: AgentState) -> AgentState:
    return await _run_specialist(state, BILLING_PROMPT, "billing")


async def tech_node(state: AgentState) -> AgentState:
    return await _run_specialist(state, TECH_PROMPT, "tech")


async def order_node(state: AgentState) -> AgentState:
    return await _run_specialist(state, ORDER_PROMPT, "order")





# ── Build and compile the graph ───────────────────────────────────────────────
def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("triage", triage_node)
    builder.add_node("billing", billing_node)
    builder.add_node("tech", tech_node)
    builder.add_node("order", order_node)
    builder.add_node("general", general_node)

    builder.set_entry_point("triage")

    builder.add_conditional_edges(
        "triage",
        route_intent,
        {
            "billing": "billing",
            "tech": "tech",
            "order": "order",
            "general": "general",
        },
    )

    builder.add_edge("billing", END)
    builder.add_edge("tech", END)
    builder.add_edge("order", END)
    builder.add_edge("general", END)

    return builder.compile()


# Module-level compiled graph — imported by agent.py
graph = build_graph()
