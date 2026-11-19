"""
test_conversations.py
=====================
Conversational (multi-turn) evaluations of the full LangGraph agent.

Run this file in its own deepeval invocation to keep ConversationalTestCase(s)
separate from single-turn LLMTestCase(s) — Confident AI requires homogeneous
test runs:

    deepeval test run tests/test_conversations.py -v -s

Store: Real AsyncPostgresStore (Supabase Postgres via DATABASE_URL in .env).
Judge: OpenRouterJudge (from conftest) — uses OPENROUTER_API_KEY + CHAT_MODEL.
Uses the pg_store / pg_graph fixtures from conftest.py.

Tests
-----
1. test_multi_turn_memory_recall — 3-turn conversation; ConversationalGEval checks
                                    coherence and accurate memory recall
"""
import uuid

import pytest

from deepeval import assert_test
from deepeval.metrics import ConversationalGEval
from deepeval.test_case import (
    ConversationalTestCase,
    MultiTurnParams,
    Turn,
)

from tests.conftest import run_turn


# ── Helpers ───────────────────────────────────────────────────────────────────

def fresh_user() -> str:
    """Generate a unique user_id per test to ensure isolation."""
    return f"e2e-{uuid.uuid4().hex[:8]}"


# ── Tests ─────────────────────────────────────────────────────────────────────

async def test_multi_turn_memory_recall(pg_store, pg_graph, judge):
    """
    Full 3-turn conversation:
      Turn 1 — Customer reports an issue
      Turn 2 — Customer says it's resolved
      Turn 3 — Customer asks what the issue was about

    ConversationalGEval (via OpenRouter judge) evaluates:
      - The assistant correctly acknowledges the issue in turn 1
      - The assistant confirms resolution in turn 2
      - The assistant accurately recalls the issue type in turn 3 (no hallucination)
    """
    user_id = fresh_user()
    conversation_turns: list[Turn] = []

    # ── Turn 1: Issue report ─────────────────────────────────────────────────
    messages = [{"role": "user", "content": "My internet connection drops every day at 6 PM sharp."}]
    reply1, _ = await run_turn(pg_graph, messages, user_id)
    conversation_turns.append(Turn(role="user",      content=messages[-1]["content"]))
    conversation_turns.append(Turn(role="assistant", content=reply1))

    # ── Turn 2: Resolution ───────────────────────────────────────────────────
    messages.append({"role": "assistant", "content": reply1})
    messages.append({"role": "user", "content": "The technician fixed it. You can mark it resolved."})
    reply2, _ = await run_turn(pg_graph, messages, user_id)
    conversation_turns.append(Turn(role="user",      content=messages[-1]["content"]))
    conversation_turns.append(Turn(role="assistant", content=reply2))

    # ── Turn 3: Recall ───────────────────────────────────────────────────────
    messages.append({"role": "assistant", "content": reply2})
    messages.append({"role": "user", "content": "Hey, what was that ticket about again?"})
    reply3, _ = await run_turn(pg_graph, messages, user_id)
    conversation_turns.append(Turn(role="user",      content=messages[-1]["content"]))
    conversation_turns.append(Turn(role="assistant", content=reply3))

    # ── DeepEval ConversationalGEval ─────────────────────────────────────────
    test_case = ConversationalTestCase(
        turns=conversation_turns,
        chatbot_role="Customer support agent with access to per-user memory storage",
        scenario=(
            "A customer reports an internet speed issue, confirms it is resolved, "
            "then asks the agent to recall what the issue was."
        ),
        expected_outcome=(
            "In turn 3, the agent accurately recalls the internet connection drop issue "
            "and confirms it was resolved. It does not fabricate details."
        ),
    )

    coherence_metric = ConversationalGEval(
        name="Multi-Turn Memory Coherence",
        model=judge,
        evaluation_params=[
            MultiTurnParams.SCENARIO,
            MultiTurnParams.EXPECTED_OUTCOME,
        ],
        criteria=(
            "Evaluate the full conversation for memory coherence. "
            "In the final turn, the assistant must accurately recall that the issue was an "
            "internet connection drop (not fabricate a different problem). "
            "It should also recognise the issue was marked resolved. "
            "Score high if the recall is accurate and grounded. "
            "Score low if the assistant claims no history or invents a different problem."
        ),
        threshold=0.7,
    )

    assert_test(test_case, [coherence_metric])
