# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- Monorepo with a TypeScript/React frontend (Vite) and a Python FastAPI backend for real-time/local audio transcription using Whisper and related audio tooling.
- Primary frontend lives at repo root under src/. There is a secondary scaffold at frontend/ used for experiments; the root app is the one wired to the backend.
- Backend is under backend/ with routes/, services/, and models/ layers. SQLite is used for persistence.

Common commands

Frontend (root app)
- Install deps
  ```bash path=null start=null
  npm install
  ```
- Run dev server (Vite on port 8080 per vite.config.ts). Ensure the backend base URL is provided to the client:
  ```bash path=null start=null
  export VITE_API_URL=http://localhost:8000
  npm run dev
  ```
- Build and preview
  ```bash path=null start=null
  npm run build
  npm run preview
  ```
- Lint TypeScript/React
  ```bash path=null start=null
  npm run lint
  ```

Backend (FastAPI)
- Create venv and install
  ```bash path=null start=null
  python -m venv .venv
  source .venv/bin/activate  # on Windows: .venv\\Scripts\\activate
  pip install -r backend/requirements.txt
  ```
- Run the dev server (minimal FastAPI app with /health)
  ```bash path=null start=null
  uvicorn backend.run_fastapi_audio_fixed:app --reload --host 0.0.0.0 --port 8000
  ```
- Alternative server entrypoints available in backend/ (see Architecture notes). If you use backend/main.py, run it as:
  ```bash path=null start=null
  python backend/main.py server
  ```

Backend tests (pytest)
- Install pytest if needed, then run the suite
  ```bash path=null start=null
  pip install pytest
  pytest backend/tests -q
  ```
- Run a single test
  ```bash path=null start=null
  pytest backend/tests/test_transcribe.py::test_health_endpoint -q
  ```

Key environment variables
- Frontend: VITE_API_URL – Base URL for the API (default fallback in code is http://localhost:8000).
- Backend (optional features):
  - OPENROUTER_API_KEY – Enables hybrid/AI chat features in certain code paths of backend/main.py.
  - MODE – Defaults to "offline"; some experimental endpoints in backend/main.py change behavior when set to "hybrid".

High-level architecture and structure

Frontend (Vite + React + TS)
- App location: src/ (root). Key pieces:
  - src/services/api.ts – Canonical client wrapper for REST calls. Endpoints used include /health, /transcribe (multipart upload), /history, /history/{id}, and /chat. The base URL derives from VITE_API_URL.
  - Vite alias: @ → ./src (see vite.config.ts and tsconfig.json). Use absolute imports like import { apiService } from '@/services/api'.
  - UI components under src/components and src/components/ui, pages under src/pages. This app is the one to run during development.
- There is also a minimal scaffold in frontend/ with its own package.json and tsconfig; it is not the main app. Prefer the root app unless explicitly working on that scaffold.

Backend (FastAPI + Whisper + SQLite)
- Layers (by directory):
  - backend/routes – API routers (e.g., health.py, transcribe.py). These are the primary, maintainable REST surfaces for health checks and file transcription.
  - backend/services – Core domain services: whisper_service (inference), vad_service (voice activity), diarization_service, noise_service, summary_service, database_service. Business logic belongs here.
  - backend/models – DB and schema helpers (e.g., database.py) and response models (e.g., transcription_models.py). SQLite is used for persistence. The database file verba_app.db is created in the current working directory when the app runs.
- Server entrypoints:
  - backend/run_fastapi_audio_fixed.py exposes a small FastAPI app (with /health and a stub /transcribe/file). This is the most reliable quick-start server to run with uvicorn during development.
  - backend/main.py contains a larger, experimental application with additional endpoints (transcriptions, reminders, chat via OpenRouter, etc.). It includes CORS and DB setup, but parts of it are in-progress and may require fixes before use. Prefer wiring routers from backend/routes into a FastAPI app for production-like behavior.

Repository signals from README.md
- The README’s Quick Start is broadly accurate for installing Python deps in backend/ and running the frontend, but the documented frontend dev port (5173) does not match the configured port (8080) in vite.config.ts. Use 8080 when running npm run dev at the repo root unless you change Vite config.

Integration notes and pitfalls
- CORS: If you use the minimal server backend.run_fastapi_audio_fixed:app, it does not set CORS. The frontend dev server runs on http://localhost:8080. If you encounter CORS errors, either run a server that enables CORS (e.g., wire routers into an app with CORSMiddleware allowing http://localhost:8080) or add the origin to the allowed list.
- Endpoint mismatch: The root frontend expects endpoints like /transcribe, /history, /history/{id}, and /chat. The minimal backend currently only exposes /health and a stub /transcribe/file. For full functionality, ensure the routers in backend/routes are included in the FastAPI app you run.
- Database location: Code initializes SQLite as verba_app.db in the process working directory. If you run uvicorn from different directories, you may end up with multiple DB files. Run from the repo root during development to keep data in a single place.
