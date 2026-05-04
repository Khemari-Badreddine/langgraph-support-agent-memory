from langgraph.store.memory import InMemoryStore
from langchain_openai import OpenAIEmbeddings
from .config import get_openrouter_api_key
import os

embeddings = OpenAIEmbeddings(
    model="openai/text-embedding-3-small",
    api_key=get_openrouter_api_key,
    base_url="https://openrouter.ai/api/v1",
)

store = InMemoryStore(
    index={
        "dims": 1536,
        "embed": embeddings,
    }
)
