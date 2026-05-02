import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import AgentRequest, AgentResponse, AgentResult

# Minimal in-memory memory store (replace with Redis/Postgres in prod)
memory_store: dict[str, list[str]] = {}

def get_memory(user_id: str) -> str:
    return " | ".join(memory_store.get(user_id, [])[-20:])

def append_memory(user_id: str, text: str):
    memory_store.setdefault(user_id, []).append(text)
    memory_store[user_id] = memory_store[user_id][-20:]


app = FastAPI(title="Customer Support Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/agent/respond", response_model=AgentResponse)
async def respond(payload: AgentRequest):
    # NOTE: This is a scaffold. Replace the graph/model call with your LangGraph flow.
    text = payload.text
    if not text:
        raise HTTPException(status_code=400, detail="text required")

    memory_context = get_memory(payload.user_id or "default")
    # Mock reply — replace with real LangGraph invocation
    reply = f"[mock reply] I received: {text[:200]}"
    append_memory(payload.user_id or "default", text)

    return AgentResponse(ok=True, result=AgentResult(id=f"msg_{int(time.time()*1000)}", text=reply, source="langgraph", toast=None))
