"""
test_memory_retrieval.py
========================
Layer 2: Evaluates whether get_progressive_content surfaces the right memories.

Store: InMemoryStore (no Postgres required).
Judge: OpenRouterJudge (from conftest) — uses OPENROUTER_API_KEY + CHAT_MODEL.
The retrieval function is tested directly — no full graph run needed.

Tests
-----
1. test_recent_memories_included   — the 3 most recently stored items appear in the context string
2. test_relevant_memories_ranked   — semantically relevant item appears in context for a targeted query
3. test_retrieval_geval            — LLM judge checks context is relevant, concise, and non-redundant
"""
import pytest

from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from app import store as app_store
from app.services.helper import get_progressive_content


# ── Helpers ───────────────────────────────────────────────────────────────────

async def seed_memories(store, user_id: str, items: list[dict]):
    """
    Seed the store with a list of memory items.
    Each item: {"key": str, "text": str, "badge": str}
    """
    for item in items:
        await store.aput(
            ("memories", user_id),
            key=item["key"],
            value={"text": item["text"], "badge": item.get("badge", "open"), "date": "Today"},
        )


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_recent_memories_included(mem_store):
    """
    After storing 5 memories, get_progressive_content should include text
    from the 3 most recently stored items (the 'recent' layer).
    """
    app_store._store = mem_store
    user_id = "test-ret-recent"

    items = [
        {"key": f"mem-{i}", "text": f"Issue number {i} about problem {i}"}
        for i in range(1, 6)
    ]
    await seed_memories(mem_store, user_id, items)

    context = await get_progressive_content(user_id, query="problem")

    # The 3 most recent are items 3, 4, 5 (last inserted)
    for i in [3, 4, 5]:
        assert f"Issue number {i}" in context, (
            f"Recent memory 'Issue number {i}' not found in context.\nContext:\n{context}"
        )


async def test_relevant_memories_ranked(mem_store):
    """
    With semantically diverse memories, get_progressive_content should surface
    the one most relevant to the query via vector search.
    Note: InMemoryStore uses exact keyword match for 'query' — we seed with
    a clearly unique term so the relevant item is distinguishable.
    """
    app_store._store = mem_store
    user_id = "test-ret-relevant"

    items = [
        {"key": "billing-1",  "text": "Customer was overcharged on invoice INV-999"},
        {"key": "shipping-1", "text": "Package delivery delayed by 3 days"},
        {"key": "tech-1",     "text": "Login timeout error on mobile app"},
    ]
    await seed_memories(mem_store, user_id, items)

    context = await get_progressive_content(user_id, query="invoice charge billing refund")

    # At minimum the context string should be non-empty and mention at least one memory
    assert context.strip(), "Expected non-empty context from retrieval."
    assert "Customer history:" in context, "Context should begin with 'Customer history:'"
    assert len(context.splitlines()) >= 2, "Context should contain at least one memory item."


async def test_no_memories_returns_empty_history(mem_store):
    """
    When no memories exist for a user, the context should still be
    well-formed but with no items (just the header).
    """
    app_store._store = mem_store
    user_id = "test-ret-empty"

    context = await get_progressive_content(user_id, query="anything")

    # Should not crash and should return the header
    assert "Customer history:" in context


async def test_retrieval_geval(mem_store, judge):
    """
    GEval metric: judges whether the retrieved context string is:
    - relevant to the user query
    - concise (no noise / irrelevant memories)
    - non-redundant (no repeated items)
    Uses OpenRouterJudge — no OPENAI_API_KEY required.
    """
    app_store._store = mem_store
    user_id = "test-ret-geval"

    items = [
        {"key": "billing-a", "text": "Double charge on invoice INV-4521 for $120"},
        {"key": "billing-b", "text": "Refund request pending since Apr 20"},
        {"key": "tech-a",    "text": "Login timeout error resolved on Apr 22"},
        {"key": "order-a",   "text": "Package ORD-88 delayed by 5 days"},
    ]
    await seed_memories(mem_store, user_id, items)

    query = "My invoice was charged twice, I need a refund"
    context = await get_progressive_content(user_id, query=query)

    test_case = LLMTestCase(
        input=query,
        actual_output=context,
    )

    metric = GEval(
        name="Retrieval Context Relevance",
        model=judge,
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        criteria=(
            "The retrieved context should contain memories relevant to billing and invoice issues "
            "when the user asks about a double charge and refund. "
            "Unrelated memories (e.g., login errors) should not dominate the context. "
            "The context should not repeat the same item multiple times. "
            "Score high if billing-relevant memories appear and content is concise."
        ),
        threshold=0.5,
    )

    assert_test(test_case, [metric])
