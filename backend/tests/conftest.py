# conftest.py — shared fixtures for all DeepEval evaluation tests.

import os
from typing import Optional, Tuple, Union

import pytest
import pytest_asyncio
from pydantic import BaseModel

from langchain_openai import ChatOpenAI

from deepeval.models.base_model import DeepEvalBaseLLM
from langgraph.store.memory import InMemoryStore

from app import store as app_store
from app.config import get_openrouter_api_key, CHAT_MODEL
from app.services.graph import build_graph
from app.services.state import AgentState


# OpenRouter DeepEval judge

class OpenRouterJudge(DeepEvalBaseLLM):
    
    # DeepEvalBaseLLM implementation that routes evaluation calls through
    # OpenRouter using the same API key and model already configured in config.py.

    def __init__(self):
        self._chat = ChatOpenAI(
            model=CHAT_MODEL,
            api_key=get_openrouter_api_key(),
            base_url="https://openrouter.ai/api/v1",
            temperature=0,  # deterministic for evaluation
        )

    def load_model(self):
        return self._chat

    def get_model_name(self) -> str:
        return f"openrouter/{CHAT_MODEL}"

    def generate(
        self, prompt: str, schema: Optional[type[BaseModel]] = None
    ) -> Tuple[Union[str, BaseModel], float]:
        if schema:
            structured = self._chat.with_structured_output(schema)
            result = structured.invoke(prompt)
            return result, 0.0
        response = self._chat.invoke(prompt)
        return response.content, 0.0

    async def a_generate(
        self, prompt: str, schema: Optional[type[BaseModel]] = None
    ) -> Tuple[Union[str, BaseModel], float]:
        if schema:
            structured = self._chat.with_structured_output(schema)
            result = await structured.ainvoke(prompt)
            return result, 0.0
        response = await self._chat.ainvoke(prompt)
        return response.content, 0.0


@pytest.fixture(scope="session")
def judge() -> OpenRouterJudge:
    """Shared OpenRouter judge instance for the whole test session."""
    return OpenRouterJudge()


# In-Memory Store fixture 

@pytest.fixture
def mem_store() -> InMemoryStore:
    """Fresh InMemoryStore per test — no Postgres required."""
    return InMemoryStore()


@pytest.fixture
def mem_graph(mem_store: InMemoryStore):
    """
    Graph wired to the in-memory store.
    Patches the module-level _store so get_store() returns our in-memory one.
    """
    app_store._store = mem_store
    graph = build_graph()
    yield graph
    app_store._store = None


# Postgres Store fixture

@pytest_asyncio.fixture(scope="function")
async def pg_store():
    """
    Spins up the real AsyncPostgresStore lifecycle.
    Reads DATABASE_URL from the environment / .env (your Supabase connection string).
    """
    async with app_store.store_lifespan():
        yield app_store.get_store()


@pytest.fixture
def pg_graph():
    """Graph using whatever store is currently live on app_store (real Postgres)."""
    return build_graph()


# Shared turn-runner helper

async def run_turn(
    graph,
    messages: list[dict],
    user_id: str,
    session_id: str = "test-session",
) -> tuple[str, AgentState]:
    """Invoke the graph for one turn and return (reply, final_state)."""
    initial_state: AgentState = {
        "messages": messages,
        "user_id": user_id,
        "session_id": session_id,
        "intent": "",
        "specialist": "",
        "trace": [],
    }
    final_state: AgentState = await graph.ainvoke(initial_state)
    reply = final_state["messages"][-1]["content"]
    return reply, final_state
