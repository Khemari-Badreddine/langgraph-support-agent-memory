from typing import Literal, TypedDict
from uuid import uuid4

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langchain.agents import create_agent
from langmem import create_manage_memory_tool, create_search_memory_tool

from app.config import get_openrouter_api_key, CHAT_MODEL, CHAT_TEMPERATURE
from app.prompts import (
    BILLING_PROMPT,
    GENERAL_PROMPT,
    ORDER_PROMPT,
    TECH_PROMPT,
    TRIAGE_PROMPT,
)
from app.store import get_store


# ── LLM (shared across all nodes) ────────────────────────────────────────────
def make_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=CHAT_MODEL,
        api_key=get_openrouter_api_key(),
        base_url="https://openrouter.ai/api/v1",
        temperature=float(CHAT_TEMPERATURE),
    )


# ── Graph state ───────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: list[dict]
    user_id: str
    session_id: str
    intent: str  # set by triage: billing | tech | order | general
    specialist: str  # human-readable name for the frontend badge
    trace: list[dict]  # list of {step, detail} for the frontend trace panel



# ── Node: Memory ────────────────────────────────────────────────────────────
async def memory_node(state: AgentState) -> AgentState:
    """
    Runs after every specialist. Extracts and stores facts unconditionally.
    The LLM doesn't decide whether to save — the harness does.
    """
    llm = make_llm()
    last_user_msg   = next(m for m in reversed(state["messages"]) if m["role"] == "user")
    last_agent_msg  = next(m for m in reversed(state["messages"]) if m["role"] == "assistant")

    extraction = await llm.ainvoke([
        {"role": "system", "content": """
            Extract factual, reusable information from this exchange.
            Return a JSON list of strings, each a single fact.
            Example: ["User reported double charge on invoice #INV-123", "User prefers email contact"]
            If nothing worth storing, return [].
            Return ONLY the JSON list, nothing else.
        """},
        {"role": "user", "content": f"""
            Customer said: {last_user_msg['content']}
            Agent replied: {last_agent_msg['content']}
        """},
    ])

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
        trace.append({"step": "memory", "detail": f"Stored {len(facts)} fact(s): {facts}", "memories_updated": True})

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
    return state["intent"]  # type: ignore[return-value]


# ── Helper: build a specialist agent with memory tools ───────────────────────
def _specialist_agent(user_id: str, system_prompt: str):
    return create_agent(
        model=make_llm(),
        tools=[
            create_manage_memory_tool(namespace=("memories", user_id)),
            create_search_memory_tool(namespace=("memories", user_id)),
        ],
        store=get_store(),
        system_prompt=system_prompt,
    )


# ── Node factory: specialist agents ──────────────────────────────────────────
async def _run_specialist(state: AgentState, system_prompt: str, node_name: str) -> AgentState:

    user_id = state["user_id"]
    agent = _specialist_agent(user_id, system_prompt)
    store = get_store()

    # Snapshot memory before the call
    before = await store.asearch(
        ("memories", user_id), query=state["messages"][-1]["content"], limit=100
    )

    result = await agent.ainvoke({"messages": state["messages"][-20:]})
    reply = result["messages"][-1].content

    # Detect memory writes
    after = await store.asearch(
        ("memories", user_id), query=state["messages"][-1]["content"], limit=100
    )
    memories_updated = len(after) > len(before)

    trace = state.get("trace", [])
    trace.append(
        {
            "step": node_name,
            "detail": f"{state['specialist']} composed response",
            "memories_updated": memories_updated,
        }
    )
    if memories_updated:
        trace.append(
            {
                "step": "memory",
                "detail": f"Memory updated by {state['specialist']}",
            }
        )

    # Append assistant reply to messages
    updated_messages = list(state["messages"]) + [
        {"role": "assistant", "content": reply}
    ]

    return {
        **state,
        "messages": updated_messages,
        "trace": trace,
    }


async def billing_node(state: AgentState) -> AgentState:
    return await _run_specialist(state, BILLING_PROMPT, "billing")


async def tech_node(state: AgentState) -> AgentState:
    return await _run_specialist(state, TECH_PROMPT, "tech")


async def order_node(state: AgentState) -> AgentState:
    return await _run_specialist(state, ORDER_PROMPT, "order")


async def general_node(state: AgentState) -> AgentState:
    return await _run_specialist(state, GENERAL_PROMPT, "general")


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
