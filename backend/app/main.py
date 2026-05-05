from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS_LIST
from app.db.migrations import run as run_migrations
from app.db.pool import close_pool
from app.routers import chat, memory, session
from app.store import store_lifespan


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    # 1. Run our migrations (sessions table)
    await run_migrations()
    # 2. Let LangGraph create its own vector store tables
    async with store_lifespan():
        yield
    # ── Shutdown ─────────────────────────────────────────────────────────────
    await close_pool()


app = FastAPI(title="Customer Support Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router,    prefix="/chat",    tags=["Chat"])
app.include_router(memory.router,  prefix="/memory",  tags=["Memory"])
app.include_router(session.router, prefix="/session", tags=["Session"])


@app.get("/health")
async def health():
    from app.db.pool import get_pool
    pool = await get_pool()
    db_ok = await pool.fetchval("SELECT 1") == 1
    return {
        "ok": db_ok,
        "db": "connected" if db_ok else "error",
        "version": "0.3.0",
    }