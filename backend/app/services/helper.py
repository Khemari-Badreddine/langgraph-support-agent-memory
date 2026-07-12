from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langmem import create_manage_memory_tool, create_search_memory_tool

from app.config import get_openrouter_api_key, CHAT_MODEL, CHAT_TEMPERATURE
from app.store import get_store

from app.services.state import AgentState


# ── LLM (shared across all nodes) ────────────────────────────────────────────
def make_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=CHAT_MODEL,
        api_key=get_openrouter_api_key(),
        base_url="https://openrouter.ai/api/v1",
        temperature=float(CHAT_TEMPERATURE),
    )


# ── Helper: build a specialist agent with memory tools ───────────────────────
def _build_specialist_agent(system_prompt: str):
    return create_agent(
        model=make_llm(),
        system_prompt=system_prompt,
    )


async def get_progressive_content(user_id, query) -> str:

    store = get_store()
    namespace = ("memories", user_id)

    # Layer 1: Most recent Memories
    all_memories = await store.alist(namespace)
    recent = [str(m.value) for m in all_memories[-3:]]

    # Layer 2: Most relevant Memories
    relevant = [
        str(m.value)
        for m in await store.asearch(namespace=namespace, query=query, limit=3)
    ]

    # Aggressive Deduplication

    seen, unique = set(), []

    for val in [*recent, *relevant]:
        if val not in seen:
            seen.add(val)
            unique.appen(val)

    return "Customer history:\n" + "\n".join(f"- {v}" for v in unique)


# ── Node factory: specialist agents ──────────────────────────────────────────
async def _run_specialist_agent(
    state: AgentState, system_prompt: str, node_name: str
) -> AgentState:

    context = get_progressive_content(
        state["user_id"], state["messages"][-1]["content"]
    )
    full_prompt = f"{system_prompt}\n\n{context}"

    agent = _build_specialist_agent(full_prompt)
    trace = state.get("trace", [])

    result = await agent.ainvoke({"messages": state["messages"][-20:]})
    reply = result["messages"][-1].content

    # Updating the trace
    trace.append(
        {
            "step": node_name,
            "detail": f"{state['specialist']} composed response",
            "memories_updated": False,
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
