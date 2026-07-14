from fastapi import APIRouter

from app.store import get_store
from app.db.migrations import delete_memory_rows

router = APIRouter()


@router.get("/{user_id}")
async def get_memory(user_id: str):
    store = get_store()
    items = await store.asearch(("memories", user_id))
    return {"memories": [item.value for item in items]}


@router.delete("/{user_id}")
async def clear_memory(user_id: str):
    cleared = await delete_memory_rows(user_id)
    return {"cleared": cleared, "user_id": user_id}
