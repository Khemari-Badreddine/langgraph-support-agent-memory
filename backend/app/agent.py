from langgraph.prebuilt import create_react_agent
from langmem import create_manage_memory_tool, create_search_memory_tool
from langchain_openai import ChatOpenAI

from app.store import store

from app.config import (
    OPENROUTER_API_KEY,
    CHAT_MODEL,
    CHAT_TEMPERATURE,
)

SYSTEM_PROMPT = """
You are a customer support agent for a SaaS platform called Customer Support Agent.

You have two memory tools:
- manage_memory  → SAVE important facts about the customer
- search_memory  → RETRIEVE past facts before every response

Rules:
1. ALWAYS call search_memory first before composing your reply.
2. Save any new fact the customer shares: complaints, preferences, personal context.
3. If an issue is mentioned again, save it with a "RECURRING:" prefix.
4. Never mention the memory tools to the customer. Use context naturally.
5. Be concise, warm, and professional.
"""


def get_model():

    return ChatOpenAI(
        model=CHAT_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=CHAT_TEMPERATURE,
    )


def build_agent(user_id: str):
    """
    Returns a LangGraph agent namespaced to the given user.
    Each user_id gets its own isolated memory namespace.
    """

    model = get_model()
    return create_react_agent(
        model=model,
        tools=[
            create_manage_memory_tool(namespace=("memories", user_id)),
            create_search_memory_tool(namespace=("memories", user_id)),
        ],
        store=store,
        prompt=SYSTEM_PROMPT,
    )
