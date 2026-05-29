---
phase: phase2
plan: 02
subsystem: core-platform
tags:
  - llm-service
  - auth
  - api
  - fastapi
  - jwt
  - streamlit
  - state-machine
requires: [phase2-01]
provides: [svc-llm, svc-auth, svc-api]
affects: [web, services]
tech-stack:
  added:
    - aiosqlite>=0.20.0
    - pyjwt>=2.8.0
  patterns:
    - AsyncOpenAI client wrapped with ModelRegistry snapshot
    - Streamlit session auth + FastAPI JWT bearer dual auth
    - FastAPI router organization with Depends(verify_token)
    - Video status state machine enforcement (VALID_TRANSITIONS)
key-files:
  created:
    - services/llm.py
    - web/auth.py
    - web/routers/__init__.py
    - web/routers/auth.py
    - web/routers/topics.py
    - web/routers/scripts.py
    - web/routers/videos.py
  modified:
    - web/app.py
    - requirements.txt
decisions:
  - "Use ModelRegistry.snapshot() for task-start model pinning"
  - "Use settings.admin_password as JWT secret (single-source auth)"
  - "Prefix all API routes under /api/ for clear namespace"
  - "All video/topic/script routers require JWT via Depends(verify_token)"
  - "PublishTaskCreate aliased as PublishQueueCreate import in videos router"
metrics:
  duration: "~15 min"
  completed_date: "2026-05-28"
  tasks: 3
  files: 9
---

# Phase 2 Plan 02: LLM Service + Auth + API + Entrypoint Summary

LLM unified service with auto-routing, dual auth (Streamlit + FastAPI JWT), and four API router modules with video state machine enforcement.

## Tasks Executed

### Task 1: Create services/llm.py
**Commit:** `7f024f0`

Created `LLMAbstract` class that auto-routes to the active model via `ModelRegistry.snapshot()`, wraps `AsyncOpenAI` client creation, and provides `chat()` with tenacity retry (3 attempts, exponential backoff, ConnectionError/TimeoutError only) and `chat_json()` with JSON response format. Exports global instances `text_llm` and `multimodal_llm`.

### Task 2: Create web/auth.py
**Commit:** `6d46e1c`

Implemented dual authentication:
- `check_auth()` for Streamlit: password prompt with `st.session_state` flag
- `verify_token()` for FastAPI: JWT bearer dependency via `OAuth2PasswordBearer`
- `create_access_token()`: HS256 with 24-hour expiry, using `settings.admin_password` as secret

### Task 3: Create web/routers/ and update web/app.py
**Commit:** `1edecc0`

Created four FastAPI router modules under `web/routers/`:
- **auth.py**: `/api/auth/token` endpoint for password-based JWT issuance
- **topics.py**: GET/POST `/api/topics` with JWT auth
- **scripts.py**: GET/POST `/api/scripts` and POST `/api/scripts/storyboards`
- **videos.py**: Full CRUD with state machine status transitions, `/api/videos/log-model-call`, `/api/videos/publish-queue`

Rewrote `web/app.py` as combined FastAPI+Streamlit entrypoint with lifespan health check and router registration. Added `/api/health` endpoint.

Updated `requirements.txt` with `aiosqlite>=0.20.0` and `pyjwt>=2.8.0`.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

```
✓ LLMAbstract created
✓ JWT token created
✓ VideoCreate model works
✓ State machine valid
✓ FastAPI app with 18 routes (/api/auth/token, /api/topics, /api/scripts, /api/videos/*, /api/health)
```

Note: JWT emits `InsecureKeyLengthWarning` because `settings.admin_password` is currently 20 bytes (test env) vs the recommended 32 bytes for HS256. The production password should be >= 32 characters to suppress this warning.

## Self-Check: PASSED

All 9 files verified present on disk, all 3 commits verified in git log, all verification steps passed.
