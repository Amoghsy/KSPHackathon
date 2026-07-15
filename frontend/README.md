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

---

## Multilingual Voice Integration & UI Enhancements

The console features a complete Multilingual Voice Interaction layer supporting **English**, **Kannada**, and **Mixed Kannada + English** speech.

### 🎙️ Voice & Speech Features

1. **Speech Input (STT)**:
   - Utilizes browser-native Web Speech API (`SpeechRecognition`).
   - Active recording indicator (halo animations, red flashing `● REC` badge in Voice Status Bar).
   - Smart silence detection (automatically stops recording after 3 seconds of silence).
   - Language-aware speech recognition (defaults to English, switches dynamically when Kannada preferred language is active).

2. **Speech Output (TTS)**:
   - High-quality backend-driven text-to-speech engine (`/api/v1/chat/tts`) using `gTTS`.
   - **Mixed Language Processing**: Automatically detects Kannada and English text runs in responses. English segments are synthesised using the English engine (for natural pronunciation), and Kannada segments/numerics/alphanumerics are processed by the Kannada engine (converting digits like `302` and `2024` into spoken Kannada words like `ಮೂರು ನೂರು ಎರಡು` so they aren't skipped). The resulting audio segments are stitched into a single MP3 stream dynamically.
   - Per-message **Speak / Stop** triggers (avatar converts to a waveform visualization when speaking).
   - Audio playback controls in the persistent Voice Status Bar (Play, Pause, Stop, Replay last message, Speed rate, Pitch, Volume adjustments).

3. **Auto-Introduction**:
   - On initial page load, the assistant displays a structured greeting card and speaks a 10-second self-introduction in the user's preferred language.

4. **Aesthetics & Motion**:
   - **Gemini-like Aurora Background**: Multi-layered drifting radial gradient blobs animate smoothly behind the message layout, adapting to dark/light modes.
   - **Dynamic Logo Glow**: The KSP seal displays active pulse halos synchronized with TTS audio playback.
   - Animated speaking waveforms for avatars and status headers.

### 🌐 Supported Languages
- **English (en-IN)**
- **Kannada (kn-IN)**
- **Auto-Detect**: Seamlessly routes Kannada script inputs to Kannada speech output and English inputs to English speech output.

### ♿ Accessibility (A11y) & Keyboard Shortcuts
- Fully compliant ARIA landmarks, roles, and status fields (`aria-live="polite"`, `role="log"`, `role="status"`).
- Keyboard tooltips for action buttons with shortcuts.
- **Shortcuts**:
  - `Ctrl + M`: Toggle Microphone (Start/Stop listening)
  - `Escape`: Stop voice playback / cancel recording
  - `Ctrl + H`: Open/Close conversation history sidebar
  - `Ctrl + Shift + N`: Start a new conversation session

### 💻 Browser Compatibility & Requirements

| Browser | Speech Recognition (STT) | Speech Synthesis (TTS) | Notes |
|---------|--------------------------|------------------------|-------|
| Google Chrome | Yes | Yes | Native webkitSpeechRecognition support |
| MS Edge | Yes | Yes | Native support |
| Safari | Yes | Yes | iOS/macOS compatibility |
| Firefox | Partial / Config | Yes | Requires enabling `media.webspeech.recognition.enable` in `about:config` |

### ⚠️ Known Limitations & Error Handling

- **Microphone Permission Denied**: Displays a non-intrusive warning toast instructing the user to allow microphone access in site settings.
- **Speech Recognition Unavailable**: Disables the microphone button, displays a tooltip indicating the browser is not supported, and warns the user.
- **Speech Synthesis (TTS) Offline**: Cascades gracefully to browser-native synthesis speech fallback if the backend TTS service returns an error or is unreachable.
- **Gemini / Database / Redis Down**: The frontend captures HTTP exceptions, renders detailed, retryable error states inside the message thread, and defaults to memory session storage on the backend to prevent crashes.


## Enterprise RBAC UX

The frontend is role-aware through `src/lib/rbac.ts`. Login stores the user role, permissions, assigned districts, and assigned police stations in the Zustand auth store. UI components should read capabilities from that centralized model instead of hardcoding role checks.

Permission flow:
- `ROLE_PERMISSIONS` mirrors the backend permission names such as `search_cases`, `crime_map`, `financial_crime`, `view_audit_logs`, and `manage_users`.
- The sidebar is generated from permissions, so inaccessible modules are hidden instead of shown as broken pages.
- The app shell protects direct route navigation and redirects unauthorized users to `/access-restricted` with the module name, current role, and required access.
- Component-level controls use `PermissionGuard`, `PermissionCard`, `PermissionTooltip`, `RestrictedButton`, and `MaskField` from `src/components/rbac/permission.tsx`.
- Backend RBAC remains authoritative. Frontend RBAC only improves UX and must not be treated as a security boundary.

Role highlights:
- Investigator: cases, assigned district intelligence, chat, crime map, network, and pattern intelligence.
- Senior Investigator: cross-district investigation, financial crime, gang detection, sensitive case access, map, and network.
- Analyst: trends, forecasts, heatmaps, district rankings, and masked sensitive fields.
- Supervisor: investigations, audit dashboard, reports, financial/network intelligence, and export.
- Policymaker: executive analytics, state trends, heatmaps, forecasts, and hidden personal identifiers.
- Admin: all permissions, user management, audit, system health, and settings.

Sensitive fields should be masked rather than removing entire pages. For example, analysts see masked victim identity, policymakers hide victim columns, and roles without sensitive access cannot request victim addresses or account details through the chat UI.
