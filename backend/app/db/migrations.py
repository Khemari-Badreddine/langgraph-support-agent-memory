from app.db.pool import get_pool

# LangGraph's AsyncPostgresStore manages its own tables via store.setup().
# We only own this one table for conversation history.
CREATE_SESSIONS = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id  TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS messages (
        id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        session_id  TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
        role        TEXT NOT NULL CHECK (role IN ('user','assistant')),
        content     TEXT NOT NULL,
        intent      TEXT,          -- assistant rows only
        specialist  TEXT,
        trace       JSONB,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS messages_session_id_id_idx ON messages (session_id, id);
    CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions (user_id);
"""


async def run() -> None:
    pool = await get_pool()
    await pool.execute(CREATE_SESSIONS)
    print("Migrations applied.")


async def load_session(session_id: str) -> list[dict]:
    """Return full message history for a session, ordered oldest first."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT role, content FROM messages WHERE session_id=$1 ORDER BY id",
        session_id,
    )
    return [{"role": r["role"], "content": r["content"]} for r in rows]


async def save_message(session_id: str, user_id: str, role: str, content: str) -> None:
    pool = await get_pool()

    # Step 1: create the session, or confirm this user owns it
    ok = await pool.fetchval(
        """
        INSERT INTO sessions (session_id, user_id)
        VALUES ($1, $2)
        ON CONFLICT (session_id) DO UPDATE
            SET user_id = EXCLUDED.user_id
            WHERE sessions.user_id = EXCLUDED.user_id
        RETURNING session_id
        """,
        session_id,
        user_id,
    )

    # Step 2: the gate
    if ok is None:
        raise PermissionError("Session belongs to a different user")

    # Step 3: only reached if the gate passed
    await pool.execute(
        "INSERT INTO messages (session_id, role, content) VALUES ($1, $2, $3)",
        session_id,
        role,
        content,
    )


async def delete_session(session_id: str) -> int:
    pool = await get_pool()
    # ON DELETE CASCADE would remove the messages too, but deleting them
    # explicitly lets us return how many messages were cleared (as before).
    result = await pool.execute(
        "DELETE FROM messages WHERE session_id=$1", session_id
    )
    await pool.execute("DELETE FROM sessions WHERE session_id=$1", session_id)
    return int(result.split()[-1])


async def delete_memory_rows(user_id: str) -> int:
    pool = await get_pool()
    result = await pool.execute(
        """
        DELETE FROM store
        WHERE prefix = $1
           OR prefix LIKE $2
        """,
        f"memories.{user_id}",
        f"memories.{user_id}.%",
    )
    return int(result.split()[-1])

async def get_session_messages(session_id: str) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT role, content, created_at FROM messages WHERE session_id=$1 ORDER BY id",
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
    