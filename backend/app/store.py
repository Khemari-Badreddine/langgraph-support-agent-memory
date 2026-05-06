from contextlib import asynccontextmanager
from typing import AsyncIterator

from langchain_openai import OpenAIEmbeddings
from langgraph.store.postgres.aio import AsyncPostgresStore

from .config import DATABASE_URL, get_openrouter_api_key

embeddings = OpenAIEmbeddings(
    model="openai/text-embedding-3-small",
    api_key=get_openrouter_api_key(),
    base_url="https://openrouter.ai/api/v1",
)

_store: AsyncPostgresStore | None = None


def get_store() -> AsyncPostgresStore:
    if _store is None:
        raise RuntimeError("Store not initialized. Run the app startup first.")
    return _store


@asynccontextmanager
async def store_lifespan() -> AsyncIterator[None]:
    global _store 
    async with AsyncPostgresStore.from_conn_string(
        DATABASE_URL,
        index={
            "dims": 1536,
            "embed": embeddings.embed_documents,
        },
    ) as store_instance:
        _store = store_instance
        await _store.setup()
        try:
            yield
        finally:
            _store = None
