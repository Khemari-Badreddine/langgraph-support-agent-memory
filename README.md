# Customer Support Agent

A full-stack demo of a multi-agent LLM customer support system. A triage agent classifies every customer message and routes it to a specialist (billing / tech / order / general), and a memory node stores per-customer long-term memory that is injected into every future reply.

## Architecture

```
customer message
       │
       ▼
   ┌──────────┐   intent: billing | tech | order | general
   │  TRIAGE  │───────────────────────────────┐
   └──────────┘                               │ conditional edge
        ┌──────────────┬──────────────┬───────────────┐
        ▼              ▼              ▼               ▼
   ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │ BILLING │   │  TECH   │   │  ORDER   │   │ GENERAL  │   ← specialist agents
   └────┬────┘   └────┬────┘   └────┬─────┘   └────┬─────┘                        
        └──────────────┴──────┬──────┴───────────────┘
                              ▼
                        ┌──────────┐
                        │  MEMORY  │  extracts new issues / resolutions,
                        └──────────┘  dedupes, stores per user
                              │
                             END
```

Built with **LangGraph** (`StateGraph`):

- **Triage** — a cheap one-word LLM call classifies intent; anything unrecognized falls back to `general`.
- **Specialists** — four agents built with `langchain.create_agent`, each with its own system prompt. Before replying, each gets **progressive context** injected: the 3 most recent memories + the top 3 vector-search-relevant memories for that user, deduplicated.
- **Memory** — runs after every reply. An LLM extracts issues as JSON (`text` / `badge: open|res` / `date`), dedupes against existing open issues (deterministic MD5 issue IDs), and resolves open issues when the customer confirms a fix (via a second LLM matching call).

## Tech stack

| Layer     | Tech |
|-----------|------|
| Backend   | Python, FastAPI, LangGraph + LangChain, asyncpg/psycopg |
| LLM       | Any model via **OpenRouter** (`CHAT_MODEL`, e.g. `openai/gpt-4o-mini`) |
| Database  | **Postgres 16 + pgvector**, run locally in Docker — conversation history + LangGraph `AsyncPostgresStore` vector store (OpenAI `text-embedding-3-small`) |
| Frontend  | Next.js 16 (App Router), React 19, Tailwind CSS 4, TypeScript |

> ⚠️ The frontend uses Next.js 16 — its APIs/conventions differ from standard Next.js. Before changing frontend code, read the bundled docs in `frontend/node_modules/next/dist/docs/` (see `frontend/AGENTS.md`).

## Repository layout

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan (migrations + store setup)
│   │   ├── config.py            # env-driven config
│   │   ├── agent.py             # graph entrypoint (run_agent)
│   │   ├── prompts.py           # system prompts for triage/specialists/memory
│   │   ├── schemas.py           # request/response Pydantic models
│   │   ├── store.py             # AsyncPostgresStore (vector memory)
│   │   ├── routers/             # /chat, /memory, /session endpoints
│   │   ├── db/                  # connection pool + migrations.py (schema + sessions/messages queries)
│   │   └── services/
│   │       ├── graph.py         # LangGraph nodes + wiring (the multi-agent graph)
│   │       ├── state.py         # AgentState TypedDict
│   │       └── helper.py        # LLM factory, specialist factory, progressive context
│   ├── tests/                   # DeepEval LLM eval tests
│   └── venv/
├── frontend/
│   └── app/
│       ├── page.tsx             # demo dashboard
│       ├── config.ts            # API base URL, intent mapping, demo users
│       └── components/          # ChatPanel, FlowPanel (trace), MemoryPanel, UserSelector
├── customer_support_agent_v3.html  # standalone static mockup (open in browser)
└── csa_agent_workflow.svg          # workflow diagram
```

## Prerequisites

1. **Python 3.11+**
2. **Node.js 20+**
3. **Docker** — runs the local Postgres database (see Setup step 1). The database needs the **pgvector** extension, which the plain `postgres` image doesn't have, so use the `pgvector/pgvector` image. Any other pgvector-enabled Postgres works too — just point `DATABASE_URL` at it. The vector store tables are created automatically by LangGraph on startup.
4. **OpenRouter API key** — for chat + embeddings.

## Quick start (already set up)

If `backend/venv`, `backend/.env`, `frontend/node_modules` and the `csa-postgres` container already exist, start the database, then use two terminals:

```bash
docker start csa-postgres
```

```bash
# Terminal 1 — backend (http://localhost:8000)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2 — frontend (http://localhost:3000)
cd frontend
npm run dev
```

Then open **http://localhost:3000**. API docs (Swagger) are at **http://localhost:8000/docs**.

## Setup (first time)

### 1. Start Postgres (Docker)

```bash
docker run -d --name csa-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v csa-pgdata:/var/lib/postgresql/data \
  pgvector/pgvector:pg16
```

The `csa-pgdata` volume keeps your data when the container is stopped or removed. Later, `docker start csa-postgres` / `docker stop csa-postgres` is all you need.

### 2. Configure the backend

Create `backend/.env` (it is gitignored — never commit it):

```env
OPENROUTER_API_KEY=sk-or-v1-...
CHAT_MODEL=openai/gpt-4o-mini
CHAT_TEMPERATURE=0.7
CORS_ORIGINS=http://localhost:3000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
```

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter key used for the chat model **and** embeddings |
| `CHAT_MODEL` | Any OpenRouter model ID |
| `CHAT_TEMPERATURE` | Sampling temperature (default `0.7`) |
| `CORS_ORIGINS` | Comma-separated allowed origins (default `http://localhost:3000`) |
| `DATABASE_URL` | Postgres connection string (the value above matches the Docker container from step 1) |

### 3. Run the backend (port 8000)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # skip if venv already exists
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

On startup it runs migrations and initializes the vector store. Verify:

```bash
curl http://localhost:8000/health
# {"ok": true, "db": "connected", "version": "0.3.0"}
```

### 4. Run the frontend (port 3000)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**. Pick a customer, send messages, and watch:

- **Flow panel** — the live agent trace: triage classification → specialist → memory writes
- **Memory panel** — that customer's stored issues (open / resolved badges)

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/respond` | Send a message `{text, user_id, session_id}` → reply + intent + specialist + trace + `memories_updated` |
| `GET` | `/memory/{user_id}` | All stored memories for a user |
| `DELETE` | `/memory/{user_id}` | Clear a user's memories |
| `GET` | `/session/{session_id}` | Full message history for a session |
| `DELETE` | `/session/{session_id}` | Delete a session's messages |
| `GET` | `/health` | DB connectivity + version |

## Memory model

Memories are stored in the LangGraph vector store under the namespace `("memories", user_id)`, each item shaped like:

```json
{ "text": "Double charge on invoice INV-123", "badge": "open", "date": "Today" }
```

- `badge: "open"` — new/unresolved issue; key = first 8 chars of MD5(text) so duplicates overwrite instead of accumulating
- `badge: "res"` — customer confirmed it's fixed; the memory node matches the confirmation back to an open issue and flips its badge

Specialists never ask for information already in a customer's history, because the memory context is injected into their system prompt before every reply.

## Tests

DeepEval LLM-evaluation tests (they run the real graph through OpenRouter, so they consume tokens). The test dependencies are not in `requirements.txt` yet, so install them once:

```bash
cd backend
source venv/bin/activate
pip install deepeval pytest pytest-asyncio   # first time only
pytest                                        # single-turn tests
deepeval test run tests/test_conversations.py -v -s   # multi-turn tests (run separately)
```

- `test_memory_modification.py` / `test_memory_retrieval.py` use an in-memory store (no Postgres needed).
- `test_whole_agent.py` / `test_conversations.py` hit the real Postgres from `DATABASE_URL`.

## Notes / gotchas

- `frontend/app/config.ts` hardcodes `API_BASE_URL = http://localhost:8000` — update it if you move the backend.
- The CORS env var is `CORS_ORIGINS` (not `ALLOW_ORIGINS`); if unset it defaults to `http://localhost:3000`.
- `backend/.env` is gitignored — keep secrets there and never commit it.
- There is no auth: any client can read/clear any user's memory by `user_id`. Fine for a local demo, not for production.
- `customer_support_agent_v3.html` and `csa_agent_workflow.svg` are local-only (gitignored); the HTML is a self-contained UI mockup with canned responses.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `RuntimeError: OPENROUTER_API_KEY not set` | `backend/.env` is missing, or you started uvicorn from outside `backend/` |
| Backend hangs/fails on startup (`Connect call failed ... 5432`) | The database isn't running: `docker start csa-postgres` (check with `docker ps`). Startup runs migrations and needs the DB |
| `extension "vector" is not available` | The Postgres image has no pgvector — use `pgvector/pgvector:pg16`, not `postgres` |
| `Address already in use` | Something is already on the port: `lsof -ti :8000 \| xargs kill` (or `:3000`) |
| Frontend shows network/CORS errors | Backend isn't running, or `CORS_ORIGINS` doesn't include `http://localhost:3000` |
| Frontend loops on `FATAL: An unexpected Turbopack error` / panic log says `Next.js package not found` | Stale build cache (usually after moving the project folder): `rm -rf frontend/.next` and restart `npm run dev` |
| `ModuleNotFoundError: deepeval` | Install the test deps (see **Tests**) |