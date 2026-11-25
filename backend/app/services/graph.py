from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field
from langgraph.graph import END, StateGraph

from app.services.state import AgentState
from app.services.helper import make_llm, _run_specialist_agent

from app.services.prompts import (
    BILLING_PROMPT,
    GENERAL_PROMPT,
    ORDER_PROMPT,
    TECH_PROMPT,
    TRIAGE_PROMPT,
    MEMORY_PROMPT,
)

from app.store import get_store
from app.config import MEMORY_MODEL


# ── Memory: what the LLM is allowed to return ────────────────────────────────
class Problem(BaseModel):
    description: str = Field(
        description="Specific description: include invoice numbers, order IDs, error names"
    )
    same_as_open_issue: str | None = Field(
        description=(
            "Copy the text of the open issue that is about the SAME problem "
            "(same feature/invoice/order). null if no open issue is about it."
        )
    )
    matches_issue_id: str | None = Field(
        description="The [id] of that open issue, or null"
    )
    customer_says_fixed: bool = Field(
        description=(
            "true only if the CUSTOMER's own words say it is resolved or working "
            "now. The agent promising or starting a fix does NOT count."
        )
    )


class MemoryExtraction(BaseModel):
    problems: list[Problem] = Field(
        description="Every support problem the customer mentions in their latest message"
    )


async def memory_node(state: AgentState) -> AgentState:
    store = get_store()
    namespace = ("memories", state["user_id"])
    trace = state.get("trace", [])

    last_user_msg = next(m for m in reversed(state["messages"]) if m["role"] == "user")
    last_agent_msg = next(
        m for m in reversed(state["messages"]) if m["role"] == "assistant"
    )

    # 1. Show the LLM the open issues *with their keys*, so it can point at them
    stored_items = await store.asearch(namespace, limit=100)
    open_items = {
        item.key: item for item in stored_items if item.value.get("badge") == "open"
    }
    open_list = "\n".join(
        f"- [{key}] {item.value.get('text', '')}" for key, item in open_items.items()
    )

    # 2. One structured call: the LLM *classifies* each problem the customer
    #    mentions; the code below decides what to store
    llm = make_llm(MEMORY_MODEL)
    llm.temperature = 0
    llm = llm.with_structured_output(MemoryExtraction)
    try:
        result = await llm.ainvoke(
            [
                {"role": "system", "content": MEMORY_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Open issues:\n{open_list or '(none)'}\n\n"
                        f"Customer said: {last_user_msg['content']}\n"
                        f"Agent replied: {last_agent_msg['content']}"
                    ),
                },
            ]
        )
        problems = result.problems
    except Exception:
        problems = []  # memory is best-effort: never break the reply

    # 3. Apply the actions
    today = datetime.now().strftime("%b %-d")
    created, resolved = 0, 0

    for problem in problems:
        match = open_items.get(problem.matches_issue_id or "")

        if problem.customer_says_fixed and match:
            # Known issue, customer confirmed it's fixed -> resolve it
            open_items.pop(match.key)  # can't resolve twice
            await store.aput(namespace, key=match.key, value={**match.value, "badge": "res"})
            resolved += 1

        elif not problem.customer_says_fixed and not match and problem.description.strip():
            # New problem -> create it
            await store.aput(
                namespace,
                key=uuid4().hex[:8],
                value={"date": today, "badge": "open", "text": problem.description.strip()},
            )
            created += 1

        # Known issue still broken -> already stored, nothing to do (dedupe)
        # fixed but no matching open issue -> nothing to resolve

    # Updating Trace
    if created or resolved:
        parts = []
        if created:
            parts.append(f"{created} stored")
        if resolved:
            parts.append(f"{resolved} resolved")
        trace.append(
            {
                "step": "memory",
                "detail": f"Memory: {', '.join(parts)}",
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
