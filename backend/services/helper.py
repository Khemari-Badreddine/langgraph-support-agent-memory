from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langmem import create_manage_memory_tool, create_search_memory_tool

from app.config import get_openrouter_api_key, CHAT_MODEL, CHAT_TEMPERATURE
from app.store import get_store

from services.state import AgentState


# ── LLM (shared across all nodes) ────────────────────────────────────────────
def make_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=CHAT_MODEL,
        api_key=get_openrouter_api_key(),
        base_url="https://openrouter.ai/api/v1",
        temperature=float(CHAT_TEMPERATURE),
    )


# ── Helper: build a specialist agent with memory tools ───────────────────────
def _build_specialist_agent(user_id: str, system_prompt: str):
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
async def _run_specialist(
    state: AgentState, system_prompt: str, node_name: str
) -> AgentState:

    user_id = state["user_id"]
    agent = _build_specialist_agent(user_id, system_prompt)
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
