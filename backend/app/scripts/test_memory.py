import asyncio

from app.agent import build_agent
from app.store import store

USER_ID = "user_123"

DIVIDER = "─" * 55


async def send(agent, message: str) -> str:
    """Send a single message and return the agent reply."""
    result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})
    return result["messages"][-1].content


async def dump_memories(user_id: str, query: str) -> None:
    """Print all memories currently stored for a user."""
    memories = await store.asearch(
        ("memories", user_id),
        query=query,
        limit=10,
    )
    if not memories:
        print("  ⚠  No memories found.")
        print("     The agent may not have triggered manage_memory.")
        print(
            "     Try a more explicit statement, e.g. 'Please note my invoice is wrong.'"
        )
        return
    for i, m in enumerate(memories, 1):
        score = f"  (score: {m.score:.3f})" if hasattr(m, "score") and m.score else ""
        print(f"  [{i}] {m.value}{score}")


async def main() -> None:
    # ── CALL 1 — First contact ───────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("CALL 1 — First contact (new customer)")
    print(DIVIDER)

    agent_session_1 = build_agent(USER_ID)
    msg1 = "Hi, my invoice #INV-123 shows $99 but it should be $89. Please fix it."
    print(f"User : {msg1}")
    reply1 = await send(agent_session_1, msg1)

    print(f"Agent: {reply1}")

    # ── MEMORY SNAPSHOT ──────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("MEMORY SNAPSHOT — after Call 1")
    print(DIVIDER)
    await dump_memories(USER_ID, "invoice billing issue")

    # ── CALL 2 — New agent instance, same store ───────────────────────────────
  
    print(f"\n{DIVIDER}")
    print("CALL 2 — New session (agent rebuilt from scratch)")
    print(DIVIDER)

    agent_session_2 = build_agent(USER_ID) 
    msg2 = "Hey, I'm back. I have another billing question."
    print(f"User : {msg2}")
    reply2 = await send(agent_session_2, msg2)
    
    print(f"Agent: {reply2}")

    # ── RESULT ───────────────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("RESULT")
    print(DIVIDER)

    invoice_recalled = "INV-123" in reply2 or "invoice" in reply2.lower()

    if invoice_recalled:
        print("✅ PASS — Agent recalled the invoice in a brand-new session.")
        print("   Memory is working. Ready for Day 2.")
    else:
        print("❌ FAIL — Agent did not reference the invoice.")
        print("   Check that manage_memory was called in Call 1 (see snapshot above).")
        print("   Try rephrasing msg1 to be more explicit about saving the fact.")

    # ── FINAL MEMORY DUMP ────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("FINAL MEMORY DUMP — all stored facts for user_123")
    print(DIVIDER)
    await dump_memories(USER_ID, "customer history preferences issues")
    print()


if __name__ == "__main__":
    asyncio.run(main())
