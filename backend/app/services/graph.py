from typing import Literal
from uuid import uuid4
import json
import hashlib
import hashlib

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



def make_issue_id(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()[:8]


async def memory_node(state: AgentState) -> AgentState:
    llm   = make_llm()
    store = get_store()
    trace = state.get("trace", [])

    last_user_msg  = next(m for m in reversed(state["messages"]) if m["role"] == "user")
    last_agent_msg = next(m for m in reversed(state["messages"]) if m["role"] == "assistant")

    # Fetch existing open issues so the LLM can avoid duplicates
    all_stored = await store.asearch(("memories", state["user_id"]))
    open_texts = [
        item.value.get("text", "")
        for item in all_stored
        if item.value.get("badge") == "open"
    ]

    extraction = await llm.ainvoke([
        {"role": "system", "content": MEMORY_PROMPT},
        {"role": "user", "content": f"""
        Existing open issues for this customer:
        {chr(10).join('- ' + t for t in open_texts) if open_texts else '(none)'}

        Customer said: {last_user_msg['content']}
        Agent replied: {last_agent_msg['content']}
        """},
    ])

    issues = json.loads(extraction.content.strip())
    if not isinstance(issues, list):
        issues = []

    stored, updated = 0, 0

    for issue in issues:
        text  = issue.get("text", "").strip()
        badge = issue.get("badge", "open")
        date  = issue.get("date", "Today")
        if not text:
            continue

        if badge == "res":
            open_items = [
                item for item in all_stored
                if item.value.get("badge") == "open"
            ]
            if open_items:
                open_texts_list = [item.value.get("text", "") for item in open_items]
                match_prompt = (
                    f"The customer just confirmed this issue is resolved:\n  {text}\n\n"
                    f"Which of the following open issues (if any) does this refer to?\n"
                    + "\n".join(f"  [{i}] {t}" for i, t in enumerate(open_texts_list))
                    + "\n\nReturn ONLY the index number (e.g. 0) of the matching issue, "
                      "or -1 if none match. No explanation, no markdown, just the number."
                )
                match_resp = await llm.ainvoke([
                    {"role": "system", "content": "You match resolved issues to open issues by index."},
                    {"role": "user", "content": match_prompt},
                ])
                try:
                    idx = int(match_resp.content.strip())
                    if 0 <= idx < len(open_items):
                        target = open_items[idx]
                        await store.aput(
                            ("memories", state["user_id"]),
                            key=target.key,
                            value={
                                "date": target.value.get("date", "Today"),
                                "badge": "res",
                                "text": target.value.get("text", ""),
                            },
                        )
                        updated += 1
                except ValueError:
                    pass
            continue

        # Open issue: store with deterministic key
        issue_id = make_issue_id(text)
        await store.aput(
            ("memories", state["user_id"]),
            key=issue_id,
            value={"date": date, "badge": "open", "text": text},
        )
        stored += 1

    if stored or updated:
        parts = []
        if stored:  parts.append(f"{stored} stored")
        if updated: parts.append(f"{updated} resolved")
        trace.append({
            "step":             "memory",
            "detail":           f"Memory: {', '.join(parts)}",
            "memories_updated": True,
        })

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
