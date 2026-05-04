from fastapi import APIRouter
from app.store import store

router = APIRouter()

@router.get("/{user_id}")
async def get_memory(user_id: str):
    items = store.search(("memories", user_id))
    return {"memories": [item.value for item in items]}