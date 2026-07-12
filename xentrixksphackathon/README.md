# Karnataka State Police - Crime Intelligence Assistant (Frontend)

This is the secure internal console for the State Crime Records Bureau (SCRB), built with React, TanStack Start, TailwindCSS, and Axios. It interfaces with the FastAPI backend to query crime databases using natural language.

## Architecture

```
React (UI Components)
   ↓
TanStack Query (Caching & State Sync)
   ↓
Axios Client (HTTP Requests & Interceptors)
   ↓
FastAPI Backend
```

## Environment Variables

The application reads its configuration from environment variables defined in `.env`. An example template is provided in `.env.example`.

| Variable            | Description                            | Default                        |
| ------------------- | -------------------------------------- | ------------------------------ |
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend router | `http://localhost:8000/api/v1` |

## Key API Endpoints Integrated

- **Authentication**: `POST /api/v1/auth/login` (generates signed JWT)
- **Dashboard Summary**: `GET /api/v1/dashboard` (retrieves KPIs, trends, and status)
- **Chat Assistant**: `POST /api/v1/chat` (processes natural-language queries)
- **Conversation Management**:
  - `GET /api/v1/conversations` (paginated and sorted session list)
  - `GET /api/v1/conversations/{id}` (hydrates a specific session history)
  - `DELETE /api/v1/conversations/{id}` (removes a session from history)
- **Case search & Accused lists**:
  - `GET /api/v1/cases/` (lists cases)
  - `GET /api/v1/accused/` (lists accused persons)

## Development Workflow

### 1. Installation

Install all dependencies using `npm`:

```bash
npm install
```

### 2. Configuration

Copy the environment template and set the backend URL:

```bash
cp .env.example .env
```

### 3. Running Locally

Run the development server:

```bash
npm run dev
```

### 4. Code Formatting & Linting

Ensure all code satisfies code standards and styles:

```bash
npm run format
npm run lint
```

### 5. Production Build

Validate the production bundle compilation:

```bash
npm run build
```
