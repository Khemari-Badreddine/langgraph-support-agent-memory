from fastapi import APIRouter
from app.store import get_store

router = APIRouter()

@router.get("/{user_id}")
async def get_memory(user_id: str):
    store = get_store()
    items = await store.asearch(("memories", user_id))
    return {"memories": [item.value for item in items]}