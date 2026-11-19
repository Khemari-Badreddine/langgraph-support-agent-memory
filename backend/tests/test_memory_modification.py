"""
test_memory_modification.py
===========================
Layer 1: Evaluates whether memory_node correctly writes and mutates memories.

Store: InMemoryStore (no Postgres required).
Judge: OpenRouterJudge (from conftest) — uses OPENROUTER_API_KEY + CHAT_MODEL.

Tests
-----
1. test_open_issue_stored        — complaint turn creates an "open" badge entry
2. test_resolved_issue_updated   — resolution turn flips the badge to "res"
3. test_no_duplicate_issue       — same complaint twice produces only one open entry
4. test_memory_content_geval     — LLM judge checks stored text is specific & accurate
"""
import pytest

from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from app import store as app_store
from tests.conftest import run_turn


# ── Helpers ───────────────────────────────────────────────────────────────────

async def get_memories(user_id: str) -> list:
    store = app_store.get_store()
    return await store.asearch(("memories", user_id))


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_open_issue_stored(mem_graph, mem_store):
    """After a complaint, at least one 'open' memory must be stored."""
    # app_store._store = mem_store
    user_id = "test-mod-open"

    messages = [{"role": "user", "content": "I was double-charged on invoice INV-789 last week."}]
    await run_turn(mem_graph, messages, user_id)

    memories = await get_memories(user_id)
    open_badges = [m for m in memories if m.value.get("badge") == "open"]
    assert open_badges, (
        f"Expected at least one 'open' memory after a billing complaint, got: {memories}"
    )


async def test_resolved_issue_updated(mem_graph, mem_store):
    """
    Two-turn flow: complaint → resolution.
    After the resolution turn the open entry must flip to 'res'.
    """
    app_store._store = mem_store
    user_id = "test-mod-resolve"

    # Turn 1 — log the issue
    messages = [{"role": "user", "content": "My login keeps timing out every morning."}]
    reply1, _ = await run_turn(mem_graph, messages, user_id)

    # Confirm open badge was created
    mems_after_t1 = await get_memories(user_id)
    assert any(m.value.get("badge") == "open" for m in mems_after_t1), \
        "Turn 1 should have created an open memory."

    # Turn 2 — resolve the issue
    messages.append({"role": "assistant", "content": reply1})
    messages.append({"role": "user", "content": "The login issue is fixed now, you can close it."})
    await run_turn(mem_graph, messages, user_id)

    mems_after_t2 = await get_memories(user_id)
    res_badges  = [m for m in mems_after_t2 if m.value.get("badge") == "res"]
    open_badges = [m for m in mems_after_t2 if m.value.get("badge") == "open"]

    assert res_badges,  "Expected at least one 'res' memory after resolution turn."
    assert not open_badges, f"Expected no remaining 'open' memories, found: {open_badges}"


async def test_no_duplicate_issue(mem_graph, mem_store):
    """
    Sending the exact same complaint twice must NOT create duplicate open entries.
    """
    app_store._store = mem_store
    user_id = "test-mod-dedup"

    complaint = "My billing statement shows an extra $50 charge for service I never used."

    # Turn 1
    messages = [{"role": "user", "content": complaint}]
    reply1, _ = await run_turn(mem_graph, messages, user_id)

    # Turn 2 — same complaint, different phrasing
    messages.append({"role": "assistant", "content": reply1})
    messages.append({"role": "user", "content": "Still seeing that $50 charge. Still unresolved."})
    await run_turn(mem_graph, messages, user_id)

    mems = await get_memories(user_id)
    open_mems = [m for m in mems if m.value.get("badge") == "open"]
    assert len(open_mems) <= 1, (
        f"Duplicate open memories detected ({len(open_mems)}): "
        + str([m.value.get("text") for m in open_mems])
    )


async def test_memory_content_geval(mem_graph, mem_store, judge):
    """
    GEval metric: the stored memory text must be specific and accurately
    reflect what the user said (invoice number, issue type, etc.).
    Uses OpenRouterJudge — no OPENAI_API_KEY required.
    """
    app_store._store = mem_store
    user_id = "test-mod-geval"

    user_input = "I was overcharged twice on invoice INV-4521. The amount was $120 each time."
    messages = [{"role": "user", "content": user_input}]
    await run_turn(mem_graph, messages, user_id)

    mems = await get_memories(user_id)
    open_mems = [m for m in mems if m.value.get("badge") == "open"]
    assert open_mems, "Expected at least one open memory to evaluate."

    stored_text = open_mems[0].value.get("text", "")

    test_case = LLMTestCase(
        input=user_input,
        actual_output=stored_text,
    )

    metric = GEval(
        name="Memory Storage Accuracy",
        model=judge,
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        criteria=(
            "The stored memory text must be specific and accurately reflect the user's complaint. "
            "It should mention the invoice number (INV-4521) and the nature of the issue (overcharge). "
            "Generic or vague descriptions should score low."
        ),
        threshold=0.6,
    )

    assert_test(test_case, [metric])
