# Karnataka State Police — AI-Powered Crime Intelligence Platform (Backend)

Welcome to the backend server repository for the **Karnataka State Police (KSP) Crime Intelligence Platform**. This backend is built using **FastAPI**, **PostgreSQL**, and **Redis**, leveraging **Google Gemini** to power an agentic crime analysis and natural language query processing system.

---

## 📋 Table of Contents
1. [Problem Statement](#-problem-statement)
2. [Key Features](#-key-features)
3. [System Architecture & Design](#-system-architecture--design)
4. [Technology Stack & Dependency Versions](#-technology-stack--dependency-versions)
5. [Project Modules & Directory Structure](#-project-modules--directory-structure)
6. [Database ER Diagram & Schema](#-database-er-diagram--schema)
7. [Setup & Execution Instructions](#-setup--execution-instructions)
    - [Running with Docker (Recommended)](#1-running-with-docker-recommended)
    - [Running Locally (Manual Setup)](#2-running-locally-manual-setup)
8. [API Documentation](#-api-documentation)
9. [Contributors](#-contributors)
10. [License](#-license)

---

## 🔍 Problem Statement
Develop an **AI-powered Crime Intelligence Platform** that enables the **Karnataka State Police** to perform intelligent crime analysis, multilingual natural language querying, criminal network visualization, pattern detection, and secure district-level data access for faster and data-driven investigations.

---

## 🌟 Key Features

*   **AI Chat Assistant**: Provides police officers with the ability to retrieve crime information using natural language queries in English, Kannada, or code-mixed formats.
*   **Intelligent Crime Search**: Searches through FIRs, accused profiles, victim statements, police stations, and crime records using AI-enabled translation and SQL translation.
*   **Criminal Network Intelligence**: Automatically visualizes relationships between accused, victims, cases, and financial transactions using graph network mapping to uncover criminal syndicates.
*   **Pattern Intelligence**: Identifies repeat offenders, recurring crime trends, and emerging hot spots for proactive policing.
*   **Financial Crime Intelligence**: Analyzes suspicious transaction records, mapping bank accounts and monetary flows linked to investigations.
*   **Crime Map & Heatmaps**: Provides interactive geographic visualisations of district-wise crime distributions and density hotspots.
*   **Crime Analytics Dashboard**: Displays real-time crime statistics, forecasts, charts, and reports for supervisors and policymakers.
*   **Secure Access Control (RBAC & ABAC)**: Secures operations using Role-Based and Attribute-Based Access Control, enforcing district-level boundaries and providing temporary cross-district request workflows.
*   **Multilingual Voice Integration**: Features Speech-to-Text (STT) on the client and custom segmented Text-to-Speech (TTS) on the server, stitching English and Kannada audio inputs/outputs.
*   **Audit Logging & Security Monitoring**: Enforces strict accountability by auditing all database accesses, SQL executions, exports, and administration actions.

---

## 🏗️ System Architecture & Design

The platform uses a **three-tier architecture** designed to meet enterprise police standards for security, speed, and intelligence.

![System Architecture](../SYSTEM DESIGN.png)

### Architectural Components

1.  **FastAPI Gateway Gateway (REST API)**: Exposes secure, asynchronous endpoints for authentication, analytics, map hotspots, graph data, and chat sessions.
2.  **Multi-Agent Orchestrator**:
    *   **Orchestrator**: Manages conversation history in Redis, parses relative pronouns, and routes requests.
    *   **Query Agent**: Uses Google Gemini to translate natural language into SQL queries, executes them safely after validation, and outputs structured, summarized text.
    *   **Network Agent**: Analyzes relations across cases using `NetworkX`, revealing shared bank accounts, recurring partners, and victim overlaps.
    *   **Pattern Agent & Risk Agent**: Clusters occurrences using geographic coordinates and time windows to generate forecasts.
    *   **Audit Agent**: Log actions into the `audit_log` table for compliance checks.
3.  **Language & Voice Processing Engine**:
    *   Kannada Text-to-Speech uses a hybrid chunking algorithm. Since standard TTS engines fail when speaking mixed English codes or numbers in Kannada context, the backend parses text into chunks, formats numeric strings into spoken Kannada words (e.g. `302` becomes `ಮೂರು ನೂರು ಎರಡು`), compiles them, and outputs unified audio.
4.  **Security Architecture (RBAC & ABAC)**:
    *   **RBAC**: Roles (`Investigator`, `Senior Investigator`, `Analyst`, `Supervisor`, `Policymaker`, `Admin`) determine page access, actions allowed, and sensitivity masking.
    *   **ABAC**: Restricts queries to the investigator's assigned district. Investigators requesting cross-district details must submit an `Access Request`, which supervisors approve for a specific duration, writing active temporary grants.

---

## 🛠️ Technology Stack & Dependency Versions

### Relational Database & Caching
*   **PostgreSQL 16**: Central transactional database.
*   **Redis 7**: Session manager, conversation memory cache, and rate-limiting store.

### Backend Stack
*   **Python 3.11** (Development Base) / **Python 3.12** (Zoho Catalyst AppSail Production Stack)
*   **FastAPI v0.115.5**: High-performance asynchronous web framework.
*   **Uvicorn v0.32.1**: ASGI server.
*   **SQLAlchemy v2.0.36**: SQL Toolkit and Object Relational Mapper (ORM).
*   **Alembic v1.14.0**: Database migration tool.
*   **Psycopg v3.2.3 (psycopg[binary])**: PostgreSQL adapter.
*   **Pydantic Settings v2.6.1**: Settings validation using environment files.
*   **Bcrypt v4.2.0** & **PyJWT v2.10.1**: Secure password hashing and JSON Web Token generation.

### AI, NLP & Speech
*   **Google GenAI SDK (google-genai >= 1.0.0)**: Interfaces with Gemini model configurations for SQL generation and query summarization.
*   **gTTS v2.5.1**: Text-to-Speech engine.
*   **Sqlparse v0.5.3**: AST SQL parsing and validation checks.

### Graph & Analytics
*   **NetworkX >= 3.0**: Graphs and network analytics.
*   **NumPy >= 1.20**: High-level mathematical operations.

---

## 📂 Project Modules & Directory Structure

```
backend/
├── alembic/                # Database migrations
│   └── versions/           # Migration revisions scripts
├── app/
│   ├── agents/             # Multi-Agent Framework
│   │   ├── audit_agent/
│   │   ├── network_agent/
│   │   ├── orchestrator/   # Context manager and orchestrator agent
│   │   ├── pattern_agent/
│   │   └── query_agent/     # NL-to-SQL engine & validator
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/  # REST route controllers (auth, cases, network, security, etc.)
│   ├── core/               # App configuration, security helpers, RBAC/ABAC middleware
│   ├── db/                 # Database initialization, sessions, and seed generators
│   ├── models/             # SQLAlchemy ORM Models
│   ├── nlp/                # Multilingual translations and Speech (TTS) modules
│   ├── schemas/            # Pydantic Schemas (Request/Response validation)
│   ├── services/           # Business logic services (Conversations, Entity resolution)
│   └── main.py             # FastAPI App Entry point & CORS/security configurations
├── docker/                 # Container configs (Dockerfile, compose)
├── scripts/                # Utility scripts (Seeding, role normalization, migrations)
├── requirements.txt        # Production Python dependencies
└── run.py                  # Local runner script
```

---

## 📊 Database ER Diagram & Schema

Below is the database relationship model of the Crime Intelligence Platform.

### Mermaid Diagram

```mermaid
erDiagram
    USERS {
        int id PK
        string username UK
        string email UK
        string employee_id UK
        string full_name
        string hashed_password
        string role
        string account_status
        boolean must_change_password
        datetime created_at
        datetime updated_at
    }
    USER_SESSIONS {
        string id PK
        int user_id FK
        string token_identifier
        string device_name
        string device_type
        string browser
        string operating_system
        string ip_address
        text user_agent
        datetime created_at
        datetime last_activity_at
        datetime expires_at
        datetime revoked_at
        int revoked_by FK
        string revoke_reason
        boolean is_active
    }
    POLICE_STATION {
        int police_station_id PK
        string name
        string district
    }
    CRIME_TYPE {
        int crime_type_id PK
        string name
    }
    CASE_MASTER {
        int case_master_id PK
        string crime_no UK
        string case_no
        date crime_registered_date
        int police_station_id FK
        int crime_type_id FK
        int police_person_id
        int case_category_id
        int gravity_offence_id
        int crime_major_head_id
        int crime_minor_head_id
        int case_status_id
        int court_id
        datetime incident_from_date
        datetime incident_to_date
        datetime info_received_ps_date
        decimal latitude
        decimal longitude
        text brief_facts
    }
    ACCUSED_MASTER {
        int accused_master_id PK
        int case_master_id FK
        string accused_name
        int age_year
        int gender_id
        string person_id
    }
    VICTIM_MASTER {
        int victim_master_id PK
        int case_master_id FK
        string victim_name
        int age_year
        int gender_id
        boolean victim_police
    }
    CASTE_MASTER {
        int caste_master_id PK
        string caste_master_name
    }
    OCCUPATION_MASTER {
        int occupation_id PK
        string occupation_name
    }
    RELIGION_MASTER {
        int religion_id PK
        string religion_name
    }
    COMPLAINANT_DETAILS {
        int complainant_id PK
        int case_master_id FK
        string complainant_name
        int age_year
        int gender_id
        int occupation_id FK
        int religion_id FK
        int caste_id FK
    }
    FINANCIAL_TRANSACTION {
        int financial_transaction_id PK
        string source_account
        string destination_account
        string bank_name
        decimal amount
        datetime transaction_date
        boolean is_suspicious
        string reason
        int case_master_id FK
        int accused_master_id FK
    }
    USER_DISTRICT_ASSIGNMENTS {
        int id PK
        int user_id FK
        string district
        int assigned_by FK
        datetime assigned_at
        boolean is_active
        datetime removed_at
        int removed_by FK
    }
    DISTRICT_ACCESS_REQUESTS {
        int id PK
        int requester_id FK
        string requested_district
        int related_case_id FK
        text reason
        int duration_hours
        string status
        datetime requested_at
        int reviewed_by FK
        datetime reviewed_at
        text review_comment
    }
    TEMPORARY_DISTRICT_PERMISSIONS {
        int id PK
        int user_id FK
        string district
        int access_request_id FK
        int approved_by FK
        datetime approved_at
        datetime expires_at
        int related_case_id FK
        boolean is_revoked
        datetime revoked_at
        int revoked_by FK
        text revocation_reason
    }
    INVESTIGATION_HISTORY {
        int id PK
        int user_id FK
        datetime timestamp
        string investigation_name
        string entity_type
        string entity_id
    }
    AUDIT_LOG {
        int id PK
        text question
        text generated_sql
        float execution_time_ms
        datetime timestamp
        text summary
        int user_id
        string username
        string role
        string api
        int response_size
        string ip_address
        string status
        string request_id
        string action
        int target_user_id
        int supervisor_id
        string district_id
        int case_id
        text reason
        string user_agent
    }

    USERS ||--o{ USER_SESSIONS : "authenticates"
    USERS ||--o{ USER_DISTRICT_ASSIGNMENTS : "has"
    USERS ||--o{ DISTRICT_ACCESS_REQUESTS : "submits"
    USERS ||--o{ TEMPORARY_DISTRICT_PERMISSIONS : "holds"
    CASE_MASTER ||--o{ ACCUSED_MASTER : "accuses"
    CASE_MASTER ||--o{ VICTIM_MASTER : "victimizes"
    CASE_MASTER ||--o{ COMPLAINANT_DETAILS : "reports"
    CASE_MASTER ||--o{ FINANCIAL_TRANSACTION : "involves"
    POLICE_STATION ||--o{ CASE_MASTER : "records"
    CRIME_TYPE ||--o{ CASE_MASTER : "categorizes"
    ACCUSED_MASTER ||--o{ FINANCIAL_TRANSACTION : "initiates"
    COMPLAINANT_DETAILS }o--|| OCCUPATION_MASTER : "works_as"
    COMPLAINANT_DETAILS }o--|| RELIGION_MASTER : "belongs_to"
    COMPLAINANT_DETAILS }o--|| CASTE_MASTER : "belongs_to"
    DISTRICT_ACCESS_REQUESTS ||--|| TEMPORARY_DISTRICT_PERMISSIONS : "authorizes"
```

### Table Schema Definitions

1.  **`users`**: Stores KSP personnel. Columns include email, employee_id, role, password hash, status.
2.  **`user_sessions`**: Session-level tracking. Links to user IDs and records IP addresses, browser information, and revocation states.
3.  **`case_master`**: Core crime cases. Contains FIR, incident dates, geolocation details, foreign keys to crime type and police station.
4.  **`accused_master`**: Suspect details related to cases. The `person_id` matches suspects across distinct FIRs.
5.  **`victim_master` & `complainant_details`**: Victim and complainant listings, capturing demographic parameters (caste, religion, occupations).
6.  **`financial_transaction`**: Tracks suspect transactions, capturing bank data, amount, destination accounts, and flag markers.
7.  **`user_district_assignments`**: Assigns police users to their default jurisdiction districts.
8.  **`district_access_requests`**: Log requests submitted by investigators for cross-district file access.
9.  **`temporary_district_permissions`**: Active time-bound tokens granting temporary cross-district access.
10. **`audit_log`**: Structured records of SQL operations, API calls, and administrative actions.

---

## 🚀 Setup & Execution Instructions

### 1. Running with Docker (Recommended)

Make sure you have **Docker** and **Docker Compose** installed on your system.

1.  **Clone the workspace** and open a terminal inside `backend/`.
2.  **Create `.env` file**:
    Copy the sample file and enter your Google Gemini API key:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` to configure your `GEMINI_API_KEY`:
    ```env
    GEMINI_API_KEY=your_actual_gemini_api_key_here
    ```
3.  **Start Services**:
    Use docker-compose to spin up PostgreSQL, Redis, pgAdmin, and the FastAPI backend:
    ```bash
    docker compose -f docker/docker-compose.yml up --build -d
    ```
4.  **Run Migrations & Seed Data**:
    Wait for the containers to pass their health checks, then execute migrations and seeding inside the backend container:
    ```bash
    docker exec -it scrb_backend alembic upgrade head
    │   # Once migrations finish, run database seeding:
    docker exec -it scrb_backend python scripts/seed_db.py
    ```

The API will now be running at `http://localhost:8000`.

---

### 2. Running Locally (Manual Setup)

#### Prerequisites
*   Python 3.11 or 3.12 installed.
*   PostgreSQL server and Redis server running locally.

#### Backend Setup

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    # Activate on Windows:
    .venv\Scripts\activate
    # Activate on Linux/macOS:
    source .venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set Environment Variables**:
    Create `.env` based on `.env.example` and fill in local database connection parameters:
    ```env
    DATABASE_URL=postgresql+psycopg://postgres:yourpass@localhost:5432/scrb_dev
    REDIS_URL=redis://localhost:6379/0
    GEMINI_API_KEY=your_gemini_api_key
    SECRET_KEY=some_long_random_string_here
    ```
5.  **Execute Database Migrations & Seeding**:
    ```bash
    alembic upgrade head
    python scripts/seed_db.py
    ```
6.  **Run Dev Server**:
    ```bash
    python run.py
    ```
    The server starts at `http://127.0.0.1:8000`.

---

## 📖 API Documentation

Once the backend is running, access the interactive API docs at:
*   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Primary Endpoints Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/login` | Authenticate user & retrieve JWT token | No |
| **POST** | `/api/v1/chat` | Send a natural language query to the Orchestrator | Yes |
| **POST** | `/api/v1/chat/tts` | Generate text-to-speech stream (mixed en/kn) | Yes |
| **GET** | `/api/v1/dashboard` | Retrieve dashboard KPI trends | Yes |
| **GET** | `/api/v1/network/` | Generate criminal relationship graph nodes & links | Yes |
| **GET** | `/api/v1/pattern/repeat-offenders` | Retrieve repeat offender analysis list | Yes |
| **POST** | `/api/v1/security/access-requests` | Submit cross-district data permission request | Yes |
| **POST** | `/api/v1/security/approve-request/{id}` | Approve temporary access request (Supervisors/Admins) | Yes |
| **GET** | `/api/v1/audit/` | Retrieve system action logs for compliance | Yes |

---

## 👥 Contributors

This platform was developed as part of the **Karnataka State Police Hackathon** by:

*   **[Your Name / Team Name]** - Lead AI & Full-Stack Developer (feel free to update)
*   **Karnataka State Police Hackathon Team**

---

## 📄 License

This project is licensed under the **MIT License** - see below:

```text
MIT License

Copyright (c) 2026 Karnataka State Police Hackathon Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
