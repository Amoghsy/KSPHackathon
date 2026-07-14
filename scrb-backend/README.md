# SCRB Intelligence Platform — Backend

> **SCRB Intelligent Conversational AI & Crime Analytics Platform**  
> Karnataka State Police Hackathon — FastAPI backend.

---

## Project Overview

The SCRB backend is a FastAPI application that powers a conversational crime analytics
assistant for the Karnataka State Police.  It exposes a versioned REST API (`/api/v1`)
consumed by the `xentrixksphackathon` Vite/TanStack frontend.

Key capabilities (built across 12 days):

| Day | Feature |
|-----|---------|
| 1 | Backend foundation — FastAPI, DB session, config |
| 2 | NL → SQL query agent (Claude) |
| 3 | Orchestrator + Redis conversation memory |
| 4 | Frontend wired to real backend (chat screen) |
| 5–12 | Network analysis, pattern detection, maps, auth, deployment |

---

## Folder Structure

```
scrb-backend/
├── alembic/              # Migration environment & versions
│   ├── env.py
│   └── versions/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/    # Feature routers (chat, cases, …)
│   │       └── router.py     # Aggregates all v1 routers
│   ├── agents/               # AI query/orchestrator agents (Day 2+)
│   ├── db/
│   │   ├── base.py           # SQLAlchemy DeclarativeBase
│   │   ├── init_db.py        # Startup DB check
│   │   ├── seed_data/        # Faker-based seed scripts
│   │   └── session.py        # Engine + get_db() dependency
│   ├── models/               # ORM models (Day 2+)
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic layer
│   ├── utils/                # Shared utilities (redis_client, etc.)
│   ├── config.py             # Pydantic Settings
│   └── main.py               # FastAPI app + lifespan
├── docker/
│   └── docker-compose.yml    # Postgres 16 + Redis 7 (local only)
├── scripts/
│   └── seed_db.py            # Populate DB with sample data
├── tests/
├── .env.example              # Environment variable template
├── alembic.ini
└── requirements.txt
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (psycopg3 format) | `postgresql+psycopg://user:pass@localhost:5432/scrb_dev` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `APP_NAME` | Human-readable app name | `SCRB Intelligence Platform` |
| `APP_ENV` | Runtime environment (`local` / `production`) | `local` |
| `SECRET_KEY` | Random secret for signing tokens (keep private!) | `a-long-random-string` |

> **Never commit `.env` to version control.**

---

## Local Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- (Optional) `pyenv` or `virtualenv` for Python version management

### 1. Clone & enter the directory

```bash
git clone <repo-url>
cd scrb-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

The docker-compose services use:
- DB user `scrb_user`, password `scrb_pass`, database `scrb_dev`

So your `.env` should read:

```env
DATABASE_URL=postgresql+psycopg://scrb_user:scrb_pass@localhost:5432/scrb_dev
REDIS_URL=redis://localhost:6379/0
APP_NAME=SCRB Intelligence Platform
APP_ENV=local
SECRET_KEY=replace-with-a-real-secret
```

### 5. Start with Docker Compose

You can start the entire infrastructure (and optionally the backend application itself) using Docker Compose.

To build and start all services (`backend`, `postgres`, `redis`, and `pgadmin`):

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

This will:
- Build the `backend` service from `docker/Dockerfile`
- Pull and start `postgres:16-alpine` and `redis:7-alpine`
- Pull and start `pgadmin4:8` on port `5050`

Alternatively, you can start only the databases and run the backend locally:

```bash
docker compose -f docker/docker-compose.yml up postgres redis -d
```

### 6. Run database migrations

To wait for Postgres to be healthy and run database migrations:

```bash
bash scripts/run_migrations.sh
```

---

## Running Locally

To run the FastAPI server on the host machine:

```bash
uvicorn app.main:app --reload
```

- API docs (Swagger): <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health check: <http://localhost:8000/health>
- pgAdmin panel: <http://localhost:5050> (credentials: `admin@scrb.local` / `adminpass`)

---

## Running Tests

```bash
pytest
```

---

## API Versioning

All application endpoints live under `/api/v1/`.  
The `/health` endpoint is at the root for infrastructure tooling compatibility.

---

## Day 3: Conversational Memory & Session Management

### Conversation Architecture
The conversation flow coordinates the request through the following steps:
1. **API Entry**: User triggers `POST /api/v1/chat` with an optional `conversation_id`.
2. **Orchestrator**: Generates a request ID and resolves the Redis session via `ConversationManager`.
3. **Context Injection**: Deterministically rewrites the user query using past context memory (`ContextInjector`).
4. **Agent Execution**: Calls `QueryAgent` with the resolved question.
5. **Entity Resolution**: Extracts entities from the query and response rows deterministically (`EntityResolver`).
6. **Session Storage**: Updates conversation history, last generated SQL, and resolved entities in Redis.
7. **Safe Logging**: Records request-response details to PostgreSQL `audit_log` without blocking responses.

### Redis Data Structure
Sessions are stored under `session:{conversation_id}` prefix as serialized JSON representing:
- `conversation_id`: unique session identifier
- `user_id`: optional user identifier
- `created_at` & `updated_at`: timestamps
- `last_question` & `last_generated_sql`: tracks the last turn metadata
- `conversation_history`: list of message turns (messages with roles `user` and `assistant`)
- `resolved_entities`: dict mapping tracking parameters (`last_case`, `last_accused`, `last_victim`, `last_station`, `last_district`, `last_crime_type`, `last_date_range`).

### Conversation Lifecycle & Expiry
- **Expiration**: Keys are written with a default Time-To-Live (TTL) of 24 hours (86,400 seconds). Any session update resets this timer.
- **Methods**: Exposed via `ConversationManager`:
  - `create_session(conversation_id, user_id=None)`: Starts tracking a new conversation.
  - `get_session(conversation_id)`: Loads conversation data.
  - `update_session(conversation_id, context)`: Updates stored state.
  - `append_message(conversation_id, message)`: Records turn history.
  - `delete_session(conversation_id)`: Removes the session.
  - `expire_session(conversation_id, seconds)`: Updates custom key TTL.

### Context Injection & Entity Resolution Flow
1. **Extraction**: After an agent execution, `EntityResolver` parses:
   - Accused IDs matching regex `\bA\d+\b`
   - Victim IDs matching regex `\bV\d+\b`
   - Case/FIR IDs matching regex `\b(?:FIR|case|no)\b[\s-]*#?([A-Za-z0-9_/]+)\b`
   - Districts matching known Karnataka districts (e.g. `Mysuru`, `Bengaluru`).
   - Crime Types (e.g. `Theft`, `Robbery`, `Cyber Crime`).
2. **Rewriting**: When a follow-up query is received, `ContextInjector` checks if the query contains references like `he`, `she`, `his`, `her`, `that case`, `only solved ones`, or a short filter phrase like `Only Bengaluru`.
3. **Reconstruction**: It rewrites the query into a fully-qualified natural language statement incorporating these parameters so the `QueryAgent` receives the full context without requiring user repetition.

### API Documentation
All endpoints are fully integrated with Swagger/OpenAPI docs at `http://localhost:8000/docs`:
- `GET /api/v1/conversations`: Fetch all sessions with pagination (`limit`, `offset`) and sorting (`sort_by`, `sort_order`).
- `GET /api/v1/conversations/{conversation_id}`: Retrieve detailed session parameters and history.
- `PATCH /api/v1/conversations/{conversation_id}`: Update metadata manually.
- `DELETE /api/v1/conversations/{conversation_id}`: Delete a session key from storage.
- `POST /api/v1/chat`: Conversational chat endpoint accepting an optional `conversation_id` inside the request body.

### Known Limitations
- In-memory fallback is used in environments where Redis is not active/available (e.g., local unit test runs) to prevent backend failure.
- Deterministic extraction uses keyword lookup; complex phrase parsing without explicitly defined keywords is not supported.


---

## Day 6: Pattern Intelligence Agent

We implemented the Pattern Intelligence Agent to analyze historical crime data across **Time**, **Location**, and **Crime Distribution**. 

### Capabilities and Endpoints
1. **Crime Trends** (`GET /api/v1/pattern/trends`): Calculates daily/weekly/monthly/yearly time series, moving averages (rolling 3-month window), overall case volume growth/decline rate (comparison of latest month against prior month), top crime types, and district-wise rankings.
2. **Hotspot Detection** (`GET /api/v1/pattern/hotspots`):
   - Runs a custom, pure-Python **DBSCAN** clustering algorithm over case coordinates (latitude/longitude) to identify density clusters (center, case count, average severity index, dominant crime).
   - Generates stylized SVG-compatible hotspot markers (`district`, `x`, `y`, `cases`, `dominant`, `trend`, `intensity`) for drawing circles on the Karnataka state outline map.
3. **Anomaly Detection** (`GET /api/v1/pattern/anomalies`): Runs Z-score analysis over chronological volumes to flag months/weeks with unexpected spikes ($|Z| > 2.0$), providing reason commentary and confidence scores.
4. **Crime Distribution** (`GET /api/v1/pattern/distribution`): Computes status ratios (Solved vs Pending), temporal distribution (hour of day, day of week, weekdays vs weekends), accused demographics (age band, gender distribution), and calculates a custom **Crime Heat Index** (cases $\times$ severity) per district.
5. **Crime Forecasting** (`GET /api/v1/pattern/forecast`): Generates next-month volume forecasts using Linear Regression ($y = mx + c$) and 3-month Moving Average, yielding projected counts and $R^2$-based confidence levels.
6. **Gemini Intelligence Briefing** (`GET /api/v1/pattern/summary`): Compiles all calculated statistical metrics into a prompt, querying Gemini to generate a concise, government-grade narrative brief for senior officials without performing direct mathematical calculation.

### Performance & Caching
- **Aggregation in SQL**: Aggregates all trend counts, district groups, and temporal stats directly in PostgreSQL using indexes (e.g. `CaseMaster.crime_registered_date`, `CaseMaster.police_station_id`, `CaseMaster.crime_type_id`) to avoid loading individual rows.
- **Redis Cache Layer**: Intercepts queries using a 15-minute Time-To-Live (TTL = 900s) on endpoint responses. Cached keys are generated from a SHA-256 hash of the query parameters.


