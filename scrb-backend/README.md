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
