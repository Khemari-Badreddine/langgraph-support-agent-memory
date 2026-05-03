"""
FastAPI entrypoint for the customer support agent.
Keep this file focused on app wiring and route definitions.
"""

from fastapi import FastAPI

from app.agent_service import chat, get_memories
from app.schemas import ChatRequest, ChatResponse, MemoryResponse


app = FastAPI(title="Customer Support Agent - Layer 1")


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    return chat(req.user_id, req.message)


@app.get("/memories/{user_id}", response_model=MemoryResponse)
async def get_memories_endpoint(user_id: str):
    return {"user_id": user_id, "memories": get_memories(user_id)}
