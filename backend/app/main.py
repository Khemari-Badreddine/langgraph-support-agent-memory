from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS_LIST

from app.routers import chat, memory

app = FastAPI(title="Customer Support Agent API")

# CORS (important for Next.js frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(memory.router, prefix="/memory", tags=["Memory"])


# Health check (super useful)
@app.get("/health")
async def health():
    return {"ok": True}