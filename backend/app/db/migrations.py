from app.db.pool import get_pool

# LangGraph's AsyncPostgresStore manages its own tables via store.setup().
# We only own this one table for conversation history.
CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  TEXT        NOT NULL,
    user_id     TEXT        NOT NULL,
    role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions (session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id    ON sessions (user_id);
"""


async def run() -> None:
    pool = await get_pool()
    await pool.execute(CREATE_SESSIONS)
    print("Migrations applied.")


async def load_session(session_id: str) -> list[dict]:
    """Return full message history for a session, ordered oldest first."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT role, content FROM sessions WHERE session_id=$1 ORDER BY created_at",
        session_id,
    )
    return [{"role": r["role"], "content": r["content"]} for r in rows]


async def save_message(session_id: str, user_id: str, role: str, content: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO sessions (session_id, user_id, role, content)
        VALUES ($1, $2, $3, $4)
        """,
        session_id,
        user_id,
        role,
        content,
    )


async def delete_session(session_id: str) -> int:
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM sessions WHERE session_id=$1", session_id
    )
    return int(result.split()[-1])


async def get_session_messages(session_id: str) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT role, content, created_at FROM sessions WHERE session_id=$1 ORDER BY created_at",
        session_id,
    )
    return [
        {
            "role": r["role"],
            "content": r["content"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]
    