# Stateful Multi-Agent Customer Support

=======================

honestly this was a fun project that took a while to finish but taught me a lot, but i built this to try out different ways for an agent to manage memory, and to trace each step of the graph as it runs. most of the work went into the memory node: early versions saved the same issue twice when a customer reworded it, and getting dedupe and resolution right took a few rewrites and, in the end, a stronger model just for that node.

=======================

The complete explanation :)

A LangGraph customer support app with per-customer issue memory. A triage agent routes each message to a specialist (billing, tech, order or general). A memory node then keeps a per-customer list of issues: it saves new ones, marks fixed ones as resolved, and never saves the same problem twice, even when the customer words it differently. Memory survives across conversations, so a returning customer doesn't have to explain the problem again.



## Demo


https://github.com/user-attachments/assets/f0b0ec58-b39f-42de-82a9-a07fd918a3fe


## Architecture

![Agent workflow](csa_agent_workflow.svg)

## Features

- **Issue memory, not chat memory.** Instead of storing raw messages, the memory node keeps a short list of *problems* per customer, each one `open` or `resolved`.
- **No duplicates.** "I was charged twice on INV-2041" and "INV-2041 still shows two charges" are recognized as the same issue.
- **Resolve and create in one message.** "The refund came through! But my order ORD-77 still hasn't shipped" resolves the billing issue and opens an order issue in the same turn.
- **Memory across sessions.** Start a new conversation and the agent still knows about the open issues.
- **Live trace.** The frontend shows each step: triage, then the specialist, then what memory changed.

## How it works

Built with **LangGraph** (`StateGraph`): `triage → specialist → memory → END`.

1. **Triage.** A cheap one-word LLM call classifies the intent as `billing`, `tech`, `order` or `general`. Anything unexpected falls back to `general`.
2. **Specialist.** Four agents built with `langchain.create_agent`, each with its own system prompt. Before replying, each one gets **progressive context** in its system prompt: the customer's 3 most recent memories plus the 3 most relevant ones from a vector search, deduplicated.
3. **Memory.** Runs after every reply, in one structured LLM call followed by plain code:
   - The LLM sees the customer's open issues **with their ids** (for example `[a1f3] Double charge on INV-2041`), the customer's message and the agent's reply.
   - For each problem the customer mentions, it fills in a Pydantic schema: a description, `matches_issue_id` (which open issue it is, or `null`), and `customer_says_fixed` (only the customer's own words count; an agent saying "refund in progress" doesn't).
   - The **code**, not the LLM, then decides what to do:

     | Matches an open issue? | Customer says it's fixed? | Action |
     |---|---|---|
     | no | no | **create** a new open issue |
     | yes | yes | **resolve** that issue |
     | yes | no | skip, since it's already stored (this is the dedupe) |
     | no | yes | skip, since there's nothing to resolve |

   The LLM only classifies; it never writes to the store directly, which makes the behavior predictable. The memory node can use a stronger model than the chat agents (`MEMORY_MODEL`), at temperature 0, because matching reworded issues is where a small model slips.

Memories live in LangGraph's `AsyncPostgresStore` (pgvector, OpenAI `text-embedding-3-small`) under the namespace `("memories", user_id)`:

```json
{ "text": "Double charge on invoice INV-2041", "badge": "open", "date": "Nov 20" }
```

Conversation history is stored separately in two Postgres tables, `sessions` and `messages`. A session belongs to one user: a request that writes to another user's session gets a `403`.

## Tech stack

| Layer     | Tech |
|-----------|------|
| Backend   | Python, FastAPI, LangGraph + LangChain, asyncpg |
| LLM       | Any model via **OpenRouter** (`CHAT_MODEL` for the agents, `MEMORY_MODEL` for memory) |
| Database  | **Postgres 16 + pgvector** in Docker: conversation history plus the LangGraph vector store |
| Frontend  | Next.js 16 (App Router), React 19, Tailwind CSS 4, TypeScript |
| Tests     | DeepEval LLM evaluations with pytest |

## Repository layout

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan (migrations + store setup)
│   │   ├── config.py            # env-driven config
│   │   ├── agent.py             # graph entrypoint (run_agent)
│   │   ├── schemas.py           # request/response Pydantic models
│   │   ├── store.py             # AsyncPostgresStore (vector memory)
│   │   ├── routers/             # /chat, /memory, /session endpoints
│   │   ├── db/                  # connection pool + migrations.py (schema + session/message queries)
│   │   └── services/
│   │       ├── graph.py         # LangGraph nodes + wiring, including the memory node
│   │       ├── prompts.py       # system prompts for triage, specialists and memory
│   │       ├── state.py         # AgentState TypedDict
│   │       └── helper.py        # LLM factory, specialist runner, progressive context
│   └── tests/                   # DeepEval LLM eval tests
├── frontend/
│   └── app/
│       ├── page.tsx             # demo dashboard
│       ├── config.ts            # API base URL, intent mapping, demo customers
│       └── components/          # ChatPanel, FlowPanel (trace), MemoryPanel, UserSelector
└── csa_agent_workflow.svg       # the diagram above
```

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Docker**, for the local Postgres. It needs the **pgvector** extension, which the plain `postgres` image doesn't have, so use `pgvector/pgvector`. Any other pgvector-enabled Postgres works too: just point `DATABASE_URL` at it.
- An **OpenRouter API key**, used for both chat and embeddings.

## Setup (first time)

### 1. Start Postgres

```bash
docker run -d --name csa-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v csa-pgdata:/var/lib/postgresql/data \
  pgvector/pgvector:pg16
```

The `csa-pgdata` volume keeps your data when the container stops. After this, `docker start csa-postgres` and `docker stop csa-postgres` are all you need.

### 2. Configure the backend

Create `backend/.env` (it is gitignored):

```env
OPENROUTER_API_KEY=sk-or-v1-...
CHAT_MODEL=openai/gpt-4o-mini
MEMORY_MODEL=openai/gpt-4o
CHAT_TEMPERATURE=0.7
CORS_ORIGINS=http://localhost:3000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
```

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter key, used for the chat models **and** embeddings |
| `CHAT_MODEL` | OpenRouter model ID for triage and the specialists |
| `MEMORY_MODEL` | Model for the memory node only. Optional, defaults to `CHAT_MODEL`. A stronger model here makes dedupe and resolution reliable |
| `CHAT_TEMPERATURE` | Sampling temperature for the chat agents (default `0.7`). The memory node always uses `0` |
| `CORS_ORIGINS` | Comma-separated allowed origins (default `http://localhost:3000`) |
| `DATABASE_URL` | Postgres connection string. The value above matches the container from step 1 |

### 3. Run the backend (port 8000)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

On startup it creates the tables and the vector store. To check it:

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

Open **http://localhost:3000**. Pick a customer and send a few messages, then watch:

- the **Flow panel**: the live trace, from triage to the specialist to memory changes
- the **Memory panel**: that customer's issues with open or resolved badges

API docs (Swagger) are at **http://localhost:8000/docs**.

## Running again later

```bash
docker start csa-postgres
```

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

## Try it

Pick **Priya Sharma** (a new customer, so memory starts empty) and send:

1. `Hi, I was charged twice on invoice INV-2041 this month.` The message goes to the Billing Agent and one open issue is saved.
2. `Also, I can't log in to my account, it keeps timing out.` This goes to Tech Support, and there are now two open issues.
3. `Just checking — INV-2041 still shows two charges.` Still two issues: no duplicate is saved.
4. `The refund for INV-2041 came through! But my order ORD-77 still hasn't shipped.` The billing issue is resolved and an order issue is opened. The trace shows `Memory: 1 stored, 1 resolved`.
5. Click **New conversation** and ask `Hey, any news on my login problem?` The agent knows about the login issue without being told again.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/respond` | Send `{text, user_id, session_id}`. Returns the reply, intent, specialist, trace and `memories_updated` |
| `GET` | `/memory/{user_id}` | All stored memories for a customer |
| `DELETE` | `/memory/{user_id}` | Clear a customer's memories |
| `GET` | `/session/{session_id}` | Full message history for a session |
| `DELETE` | `/session/{session_id}` | Delete a session and its messages |
| `GET` | `/health` | Database connectivity and version |

## Tests

DeepEval LLM evaluations. They call the real models through OpenRouter, so they use tokens. The test dependencies aren't in `requirements.txt`, so install them once:

```bash
cd backend
source venv/bin/activate
pip install deepeval pytest pytest-asyncio
```

```bash
pytest
```

```bash
deepeval test run tests/test_conversations.py -v -s
```

The first command runs the single-turn tests, and the second runs the multi-turn tests separately.

- `test_memory_modification.py` and `test_memory_retrieval.py` use an in-memory store, so they don't need Postgres.
- `test_whole_agent.py` and `test_conversations.py` use the real Postgres from `DATABASE_URL`.

### Results

3 runs of the suite with `CHAT_MODEL=openai/gpt-4o-mini` and `MEMORY_MODEL=openai/gpt-4o`:

| Area | Tests | Passed |
|------|-------|--------|
| Create issue | `test_open_issue_stored`, `test_memory_content_geval` | 6/6 |
| Dedupe | `test_no_duplicate_issue` | 3/3 |
| Resolve | `test_resolved_issue_updated`, `test_multi_turn_memory_recall` | 6/6 |
| Cross-session | none yet | not tested |
| Retrieval | 4 tests in `test_memory_retrieval.py` | 12/12 |
| Triage + replies | 6 tests in `test_whole_agent.py` | 16/18 |

The 2 failures were the same case: the login message was routed to Tech correctly, but the judge scored the reply below threshold (0.3 and 0.5 vs 0.6) because it had no troubleshooting steps.

## Limitations

- **No auth.** Any client can read or clear any customer's memory by `user_id`. That's fine for a local demo, not for production.
- The specialists don't call real billing, order or account systems; they reply from their prompt and the customer's memory.
- `frontend/app/config.ts` hardcodes `API_BASE_URL = http://localhost:8000`. Change it if you move the backend.

**What I'd do next:** give the specialists real tool calls to a billing/order API, and add auth so each customer only sees their own data.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `RuntimeError: OPENROUTER_API_KEY not set` | `backend/.env` is missing, or uvicorn was started from outside `backend/` |
| Backend fails on startup with `Connect call failed ... 5432` | The database isn't running: `docker start csa-postgres` (check with `docker ps`) |
| `extension "vector" is not available` | The image has no pgvector. Use `pgvector/pgvector:pg16`, not `postgres` |
| `Address already in use` | Something is already on the port: `lsof -ti :8000 \| xargs kill` (or `:3000`) |
| Frontend shows network or CORS errors | The backend isn't running, or `CORS_ORIGINS` doesn't include `http://localhost:3000` |
| Frontend loops on `An unexpected Turbopack error` and the log says `Next.js package not found` | Stale build cache, usually after moving the project folder: `rm -rf frontend/.next`, then restart `npm run dev` |
| `ModuleNotFoundError: deepeval` | Install the test dependencies (see **Tests**) |
