from typing import Literal
from uuid import uuid4
import json

from langgraph.graph import END, StateGraph

from app.services.state import AgentState
from app.services.helper import make_llm, _run_specialist_agent

from app.prompts import (
    BILLING_PROMPT,
    GENERAL_PROMPT,
    ORDER_PROMPT,
    TECH_PROMPT,
    TRIAGE_PROMPT,
    MEMORY_PROMPT,
)

from app.store import get_store


# ── Node: Memory ────────────────────────────────────────────────────────────
async def memory_node(state: AgentState) -> AgentState:
    """
    Runs after every specialist. Extracts and stores facts unconditionally.
    The LLM doesn't decide whether to save — the harness does.
    """
    llm = make_llm()
    store = get_store()
    trace = state.get("trace", [])

    last_user_msg = next(m for m in reversed(state["messages"]) if m["role"] == "user")
    last_agent_msg = next(
        m for m in reversed(state["messages"]) if m["role"] == "assistant"
    )

    extraction = await llm.ainvoke(
        [
            {
                "role": "system",
                "content": MEMORY_PROMPT,
            },
            {
                "role": "user",
                "content": f"""
            Customer said: {last_user_msg['content']}
            Agent replied: {last_agent_msg['content']} """,
            },
        ]
    )

    try:
        facts = json.loads(extraction.content.strip())
    except Exception:
        facts = []

    # Saving memories with aggresive Deduplication
    for fact in facts:
        
        existing = await store.asearch(
            ("memories", state["user_id"]), query=fact, limit=1
        )

        if existing and existing[0].score > 0.9:
            continue

        await store.aput(
            ("memories", state["user_id"]),
            key=str(uuid4()),
            value={"text": fact, "intent": state["intent"]},
        )

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
    return await _run_specialist_agent(state, GENERAL_PROMPT, "general")


async def billing_node(state: AgentState) -> AgentState:
    return await _run_specialist_agent(state, BILLING_PROMPT, "billing")


async def tech_node(state: AgentState) -> AgentState:
    return await _run_specialist_agent(state, TECH_PROMPT, "tech")


async def order_node(state: AgentState) -> AgentState:
    return await _run_specialist_agent(state, ORDER_PROMPT, "order")


# ── Build and compile the graph ───────────────────────────────────────────────
def build_graph():
    builder = StateGraph(AgentState)

    # Helper Nodes
    builder.add_node("triage", triage_node)
    builder.add_node("memory", memory_node)

    # Main Nodes
    builder.add_node("billing", billing_node)
    builder.add_node("tech", tech_node)
    builder.add_node("order", order_node)
    builder.add_node("general", general_node)

    # Graph Starts
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

    builder.add_edge("billing", "memory")
    builder.add_edge("tech", "memory")
    builder.add_edge("order", "memory")
    builder.add_edge("general", "memory")

    builder.add_edge("memory", END)

    return builder.compile()


# Module-level compiled graph — imported by agent.py
graph = build_graph()
