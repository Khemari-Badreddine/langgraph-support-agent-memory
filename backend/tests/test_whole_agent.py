"""
test_whole_agent.py
===================
Layer 3: End-to-end evaluation of the full LangGraph agent.

Store: Real AsyncPostgresStore (Supabase Postgres via DATABASE_URL in .env).
Judge: OpenRouterJudge (from conftest) — uses OPENROUTER_API_KEY + CHAT_MODEL.
Uses the pg_store / pg_graph fixtures from conftest.py.

All tests here use single-turn LLMTestCase(s). Conversational (multi-turn)
tests live in test_conversations.py and must be run as a separate deepeval
invocation — Confident AI does not allow mixing LLMTestCase and
ConversationalTestCase in the same test run.

Tests
-----
1. test_triage_routing         — intent classification for billing/tech/order/general
2. test_answer_relevancy       — DeepEval AnswerRelevancyMetric on a billing reply
3. test_no_hallucination_geval — new user should NOT get fabricated history
"""
import uuid

import pytest

from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

from tests.conftest import run_turn


# ── Helpers ───────────────────────────────────────────────────────────────────

def fresh_user() -> str:
    """Generate a unique user_id per test to ensure isolation."""
    return f"e2e-{uuid.uuid4().hex[:8]}"


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("user_input,expected_intent", [
    ("I was charged twice on my last invoice.",         "billing"),
    ("I can't log into my account, it keeps timing out.", "tech"),
    ("Where is my order? It should have arrived Monday.", "order"),
    ("Hello, I just wanted to say your service is great.", "general"),
])
async def test_triage_routing(pg_store, pg_graph, judge, user_input: str, expected_intent: str):
    """
    The triage node must correctly classify intent for each message category.
    Uses GEval (via OpenRouterJudge) as a secondary check on reply appropriateness.
    """
    user_id = fresh_user()
    messages = [{"role": "user", "content": user_input}]

    reply, final_state = await run_turn(pg_graph, messages, user_id)

    # Hard assertion: intent must be correct
    assert final_state["intent"] == expected_intent, (
        f"Expected intent '{expected_intent}', got '{final_state['intent']}'. "
        f"Input: '{user_input}'"
    )

    # Soft assertion: GEval checks the reply is appropriate for the intent
    test_case = LLMTestCase(
        input=user_input,
        actual_output=reply,
    )
    metric = GEval(
        name="Intent-Appropriate Response",
        model=judge,
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        criteria=(
            f"The user sent a '{expected_intent}' message. "
            "The assistant's reply should be relevant and appropriate for that topic. "
            "It should NOT address a completely unrelated topic."
        ),
        threshold=0.6,
    )
    assert_test(test_case, [metric])


async def test_answer_relevancy(pg_store, pg_graph, judge):
    """
    AnswerRelevancyMetric: the agent's reply to a billing question must be
    relevant to the input (score ≥ 0.7). Routes evaluation through OpenRouter.
    """
    user_id = fresh_user()
    user_input = "I see a charge of $89 on my account that I don't recognise. Can you help?"
    messages = [{"role": "user", "content": user_input}]

    reply, _ = await run_turn(pg_graph, messages, user_id)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=reply,
    )
    metric = AnswerRelevancyMetric(threshold=0.7, model=judge, include_reason=True)
    assert_test(test_case, [metric])


async def test_no_hallucination_geval(pg_store, pg_graph, judge):
    """
    For a brand new user with NO stored history, the agent must NOT fabricate
    past interactions or pretend to remember previous tickets.
    Routes evaluation through OpenRouter via judge fixture.
    """
    user_id = fresh_user()
    user_input = "Hi, I'm a new customer. I just signed up and have a question about billing."
    messages = [{"role": "user", "content": user_input}]

    reply, _ = await run_turn(pg_graph, messages, user_id)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=reply,
    )
    metric = GEval(
        name="No Memory Hallucination",
        model=judge,
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        criteria=(
            "The user is brand new and has no prior history. "
            "The assistant must NOT reference any previous tickets, past issues, or earlier conversations. "
            "A good response greets the customer and asks how it can help with the billing question. "
            "Any fabricated history should score very low."
        ),
        threshold=0.7,
    )
    assert_test(test_case, [metric])



