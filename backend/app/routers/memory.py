from fastapi import APIRouter

from app.store import get_store

router = APIRouter()

# asearch() returns only 10 items unless a limit is passed.
MAX_MEMORIES = 500


@router.get("/{user_id}")
async def get_memory(user_id: str):
    store = get_store()
    items = await store.asearch(("memories", user_id), limit=MAX_MEMORIES)
    return {"memories": [item.value for item in items]}


@router.delete("/{user_id}")
async def clear_memory(user_id: str):
    # Go through the store API instead of raw SQL on LangGraph's internal tables.
    store = get_store()
    namespace = ("memories", user_id)
    cleared = 0
    while items := await store.asearch(namespace, limit=MAX_MEMORIES):
        for item in items:
            await store.adelete(namespace, item.key)
        cleared += len(items)
    return {"cleared": cleared, "user_id": user_id}
