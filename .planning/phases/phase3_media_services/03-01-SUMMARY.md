---
phase: 03-media_services
plan: 01
subsystem: "Media Services"
tags: ["voice", "image-gen", "digital-human", "broll", "publisher", "model-logger", "dialect-dict", "knowledge-base"]
requires: ["core-data-models", "model-registry"]
provides: ["voice-generation", "image-generation", "digital-human", "video-generation", "multi-platform-publisher", "model-call-logging", "dialect-dictionary"]
affects: ["composer", "workflow", "content-agent"]
tech-stack:
  added:
    - "httpx.AsyncClient singleton in services/__init__.py"
    - "aiosqlite for model call logging"
    - "pytest-asyncio for async test support"
  patterns:
    - "Strategy dispatch via dict lookup (not if/elif)"
    - "ModelRegistry.snapshot() for model routing"
    - "Mock fallback when no API key configured"
    - "T-03-01: API key stripping from error messages"
    - "T-03-02: pending_review default status on publish"
key-files:
  created:
    - "services/__init__.py (updated)"
    - "services/model_logger.py"
    - "services/voice.py"
    - "services/image_gen.py"
    - "services/digital_human.py"
    - "services/video_gen.py"
    - "services/publisher.py"
    - "tests/test_services/conftest.py"
    - "tests/test_services/test_voice.py"
    - "tests/test_services/test_image_gen.py"
    - "tests/test_services/test_digital_human.py"
    - "tests/test_services/test_video_gen.py"
    - "tests/test_services/test_publisher.py"
    - "data/dialect_dict.json"
    - "data/knowledge_base.md"
    - "tests/test_data.py"
  modified:
    - "services/__init__.py (shared httpx client and log_model_call re-export)"
decisions:
  - "MiniMax is only registered as fallback, not active_id (architecture rule)"
  - "publisher returns pending_review by default for unattended safety (T-03-02)"
  - "API keys stripped from error messages before logging (T-03-01)"
  - "Mock mode uses FFmpeg for audio/video and pure-Python PNG for images"
  - "Digital human manual mode writes JSON instructions instead of generating video"
metrics:
  duration: "~30 minutes"
  completed_date: "2026-05-28"
---

# Phase 3 Plan 1: Media Services Summary

**One-liner:** Built all six media generation services (voice, image, digital human, B-roll, publisher, model logger) with strategy-pattern dispatch via ModelRegistry, mock fallback for all providers, and 22 passing tests.

---

## Tasks Completed

### Task 1: Shared Infrastructure
- **Files:** `services/__init__.py`, `services/model_logger.py`
- **Commit:** `5d1576c`
- Created `model_logger.py` with `log_model_call()` async function and `Timer` context manager
- API key stripping in error messages (T-03-01 mitigation: regex-based redaction of `api_key`, `secret`, `token`, `authorization`, `bearer` patterns)
- Database errors logged as warnings, never raised
- Shared `httpx.AsyncClient` singleton in `services/__init__.py` with 120s timeout, 20 max connections
- Re-exported `log_model_call` and `Timer` from package for convenient import

### Task 2: Voice and Image Generation
- **Files:** `services/voice.py`, `services/image_gen.py`, `tests/test_services/conftest.py`, `tests/test_services/test_voice.py`, `tests/test_services/test_image_gen.py`
- **Commit:** `49ccf70`
- Voice: `VOICE_PROVIDERS` dict mapping 8 providers (mimo_voiceclone, mimo_tts, mimo_voicedesign, elevenlabs_tts, cartesia_tts, openai_tts, minimax_speech, mock)
- MiMo provider POSTs to `{api_base}/v1/audio/speech`; MiniMax POSTs to `/t2a_v2` with warning log
- Image: `IMAGE_PROVIDERS` dict with gpt_image2_relay and mock
- Minimal pure-Python PNG generator (no PIL dependency) for mock mode
- Fallback chain through `model.fallback_ids` with ultimate mock fallback
- 7 passing tests (4 voice, 3 image)

### Task 3: Digital Human, B-roll, Publisher
- **Files:** `services/digital_human.py`, `services/video_gen.py`, `services/publisher.py`, plus 3 test files
- **Commit:** `dafabdb`
- Digital human: mock (Ken Burns FFmpeg), local, manual (JSON instructions), heygen (API POST), and 3 NotImplementedError providers with fallback
- B-roll: mock (zoompan FFmpeg), local, 6 paid providers as NotImplementedError
- Publisher: dict dispatch by platform (douyin/kuaishou via API, weixin/xiaohongshu via Playwright)
- T-03-02 safety: all published videos default to `pending_review` status
- 9 passing tests (2 digital human, 3 video, 4 publisher)

### Task 4: Data Files and Validation
- **Files:** `data/dialect_dict.json`, `data/knowledge_base.md`, `tests/test_data.py`
- **Commit:** `fbde0f1`
- Dialect dictionary: 23 entries across categories (daily_life, grammar, people) with pinyin, meaning, example
- Knowledge base: 7 sections covering geography, dialect, food, customs, attractions, notable figures, viral trends (62 lines)
- 6 passing data tests (schema validation, minimum entries, section counts)

---

## Verification Results

| # | Check | Status |
|---|-------|--------|
| 1 | `from services import get_http_client, log_model_call` | PASS |
| 2 | All 16 service tests pass | PASS |
| 3 | All 6 data tests pass | PASS |
| 4 | Strategy dispatch via `.get(model.id)` pattern (no if/elif) | PASS |
| 5 | MiniMax only in fallback, never active_id | PASS |
| 6 | All services use shared `get_http_client()` from services package | PASS |
| 7 | All services call `log_model_call` on success and failure | PASS |

---

## Deviations from Plan

### Auto-fix (Rule 1) — pytest-asyncio not installed

- **Issue:** Async test functions caused `PytestUnknownMarkWarning` and failed
- **Fix:** Added `pytest-asyncio` to venv
- **Commit:** 49ccf70

### Auto-fix (Rule 1) — log_model_call not re-exported from services package

- **Issue:** `from services import log_model_call` failed because `__init__.py` only had `get_http_client`
- **Fix:** Added `from services.model_logger import log_model_call, Timer` and `__all__` to `__init__.py`
- **Commit:** 4135b42

---

## Known Stubs

None. Mock mode is intentional and documented — not a placeholder. All paid providers with NotImplementedError have fallback chains to mock. Tests verify the mock paths work correctly.

---

## Threat Flags

None. All threat register items were either mitigated (T-03-01 API key stripping, T-03-02 pending_review gate) or accepted (T-03-04, T-03-05) as documented in the plan.

---

## Requirements Covered

- **SVC-02** (Voice Generation): voice.py with 8 providers + mock
- **SVC-03** (Digital Human): digital_human.py with 7 modes
- **SVC-04** (B-roll Video): video_gen.py with 8 providers
- **SVC-05** (Image Generation): image_gen.py with GPT-image-2 relay + mock
- **SVC-07** (Multi-platform Publishing): publisher.py with 4 platforms
- **DATA-06** (Dialect Dictionary): dialect_dict.json with 23 entries
- **DATA-07** (Knowledge Base): knowledge_base.md with 7 sections
- **CHECK-07** (Database Logging): model_logger.py inserts to model_call_logs
