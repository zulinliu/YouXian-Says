---
phase: phase7
plan: "01"
subsystem: "test-and-acceptance"
tags:
  - testing
  - acceptance
  - integration
requires:
  - phase2_core_platform-01
  - phase3_media_services-01
  - phase4_agent_orchestration-01
provides:
  - test-llm-service
  - test-voice-service
  - test-composer-service
  - test-api-connection
affects:
  - youxianduanshipin/tests/test_services/test_llm.py
  - youxianduanshipin/tests/test_services/test_voice.py
  - youxianduanshipin/tests/test_services/test_composer.py
  - youxianduanshipin/web/pages/settings.py
  - youxianduanshipin/pyproject.toml
tech-stack:
  added: []
  patterns:
    - structured tests with structural/API/mock separation
    - pytest markers for API-key-dependent and slow tests
key-files:
  created:
    - youxianduanshipin/tests/test_services/test_llm.py
    - youxianduanshipin/tests/test_services/test_composer.py
  modified:
    - youxianduanshipin/tests/test_services/test_voice.py
    - youxianduanshipin/web/pages/settings.py
    - youxianduanshipin/pyproject.toml
decisions:
  - test_api_connection function signature changed from (model_config: dict) to (api_base, model_name, api_key, env_key, provider) to support httpx-based connectivity check
  - SRT translation field not rendered in SRT (by design — SRT shows dialect text; translation is metadata)
  - pytest asyncio_mode=auto set in pyproject.toml to fix async test compatibility
metrics:
  duration: "~2m"
  completed: "2026-05-29"
---

# Phase 7 Plan 01: Final Tests and Acceptance

Test suite enhancements for LLM service, voice service, composer service, and API connectivity check. All tests run without API keys by using structural tests and pytest markers.

## Tasks Executed

| # | Name | Type | Commit |
|---|------|------|--------|
| 1 | tests/test_services/test_llm.py | auto | 92fa3aa |
| 2 | tests/test_services/test_voice.py (enhance) | auto | 1323f4b |
| 3 | tests/test_services/test_composer.py | auto | 5372065 |
| 4 | test_api_connection enhancement (CHECK-02) | auto | 730171c |

## Results

### Test Summary

All 61 tests pass (non-slow, non-API). Breakdown:

- **test_llm.py**: 7 passed (1 skipped as @pytest.mark.api) — structure, imports, retry decorator, mock client
- **test_voice.py**: 7 passed — 4 existing + 3 new (import, provider dispatch, mock fallback)
- **test_composer.py**: 8 passed (3 slow tests run separately) — SRT generation (6 tests), imports (2 tests)
- **test_mock_pipeline.py (slow)**: 3 passed — SRT format, resolution 1080x1920, no API keys needed
- **All other tests**: 36 passed — model registry, data, agents, web admin, publisher, etc.

### test_api_connection (CHECK-02)

- Enhanced from stub (URL-only validation) to real httpx-based connectivity check
- OpenAI-compatible providers: tries GET /models endpoint
- Media providers: tries URL reachability
- Falls back to format-only validation when no credentials
- Gracefully handles DNS errors, timeouts, and HTTP errors

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 1 - Bug] test_get_client_structure failed because AsyncOpenAI requires api_key
   - **Found during:** Task 1
   - **Issue:** ModelRegistry.snapshot() returns model with empty resolved_api_key, causing AsyncOpenAI to raise OpenAIError
   - **Fix:** Used MockModelOption with resolved_api_key="sk-test-dummy" via monkeypatching ModelRegistry.snapshot
   - **Files modified:** tests/test_services/test_llm.py
   - **Commit:** 92fa3aa

2. [Rule 1 - Bug] async tests failed with "async def functions are not natively supported"
   - **Found during:** Task 1
   - **Issue:** pytest-asyncio requires either @pytest.mark.asyncio on each test or asyncio_mode=auto in config
   - **Fix:** Added asyncio_mode = "auto" to pyproject.toml and registered "api" marker
   - **Files modified:** youxianduanshipin/pyproject.toml
   - **Commit:** 92fa3aa

3. [Rule 1 - Test] test_generate_srt_dialect_word asserted that "translation" field content appears in SRT output
   - **Found during:** Task 3
   - **Issue:** _generate_srt only outputs the "text" field by design. Translation field is metadata, not SRT content.
   - **Fix:** Removed assertion on "好吃" from SRT content; documented design intent in test docstring
   - **Files modified:** tests/test_services/test_composer.py
   - **Commit:** 5372065

## Success Criteria

- [x] Task 1: tests/test_services/test_llm.py — 7 structure/import/retry/mock tests + 2 API-key tests (skipped by default)
- [x] Task 2: tests/test_services/test_voice.py — 3 additional tests (import, provider dispatch, mock fallback)
- [x] Task 3: tests/test_services/test_composer.py — 11 tests (SRT:6, imports:2, mock pipeline:3)
- [x] Task 4: test_api_connection enhanced with real httpx-based connectivity check

## Self-Check: PASSED
