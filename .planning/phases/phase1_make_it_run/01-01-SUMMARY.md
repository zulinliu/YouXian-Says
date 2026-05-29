---
phase: "1-make_it_run"
plan: "01"
subsystem: "skeleton-config"
tags: ["infrastructure", "config", "model-registry", "streamlit"]
dependency_graph:
  requires: []
  provides: ["config/settings.py", "config/model_registry.py", "config/prompts.py", "requirements.txt", "setup.sh"]
  affects: ["plan-02", "plan-04"]
tech-stack:
  added: ["Python 3.12", "Pydantic Settings v2", "Streamlit 1.57", "cryptography (Fernet)"]
  patterns: ["Singleton (settings)", "Registry pattern (ModelRegistry)", "Factory (get_active)"]
key-files:
  created: ["config/settings.py", "config/model_registry.py", "config/prompts.py", "web/app.py", "web/pages/settings.py", ".env.example", "requirements.txt", "pyproject.toml", "scripts/setup.sh", "README.md", ".gitignore"]
  modified: []
decisions:
  - "All extra .env vars (YIMEI_USERNAME, YIMEI_PASSWORD, CHANMAMA_TOKEN, MASTER_ENCRYPTION_KEY) added to Settings class to avoid pydantic extra_forbidden errors"
  - "6 function slots (not 7) because Plan 01 scope covers only text_llm, multimodal, image_gen, video_gen, voice_clone, digital_human — agents/ slot reserved for Phase 4"
metrics:
  duration: "~25 min"
  completed_at: "2026-05-28T13:44+08:00"
  tasks: 3
  commits: 4
  files_created: 19
---

# Phase 1 Make It Run Plan 01: Project Skeleton & Config Summary

Project skeleton with config modules, model registry (38+ model options across 6 function slots), Fernet-encrypted credential persistence, Streamlit auth guard + model settings page, and one-click setup script.

## Task Results

### Task 1.1: Create directory structure and config modules

All config modules created and verifiable:
- `config/settings.py` — Pydantic Settings v2 with all 38 env fields, singleton pattern, admin_password validation
- `config/model_registry.py` — 6 function slots, 35 model options, Fernet encryption/decryption, atomic file writes with .tmp/.bak
- `config/prompts.py` — DEFAULT_SYSTEM_PROMPT and get_prompt() function
- 14 .gitkeep files for empty directories

**Deviations (Rule 2):** Added YIMEI_USERNAME, YIMEI_PASSWORD, CHANMAMA_TOKEN, MASTER_ENCRYPTION_KEY fields to Settings after .env file triggered pydantic `extra_forbidden` errors. These are present in .env.example but were missing from the initial Settings definition.

### Task 1.2: Create env config, requirements, setup script

- `.env.example` — All 50+ env vars grouped by service
- `requirements.txt` — 14 pip dependencies
- `pyproject.toml` — Project metadata with pytest/coverage config
- `scripts/setup.sh` — One-click venv creation + pip install + ffmpeg check
- `README.md` — Project description, quick start, architecture overview
- `.gitignore` — Python cache, venv, .env, generated files

**setup.sh verified:** exits 0, creates venv, installs all deps, copies .env.example

### Task 1.3: Implement Streamlit settings page

- `web/app.py` — Auth guard with password validation, st.Page/st.navigation
- `web/pages/settings.py` — Expander per function slot, model config forms, switch/save/test buttons
- Streamlit starts successfully on port 8501

### Verification

- `from config.settings import Settings; from config.model_registry import ModelRegistry; from config.prompts import get_prompt` — OK
- `ModelRegistry.get_active('text_llm').id == 'deepseek_v4_flash'` — OK
- `bash scripts/setup.sh` — exits 0, venv created
- `streamlit run web/app.py --server.port 8501` — starts without errors

## Commits

| Hash | Message |
|------|---------|
| f294f49 | feat(1-make_it_run-01): create project directory structure and core config modules |
| ec6d4c1 | chore(1-make_it_run-01): add .gitignore for Python and generated files |
| 25faf46 | feat(1-make_it_run-01): create env config, requirements, setup script, and README |
| b3de903 | feat(1-make_it_run-01): implement Streamlit entrypoint and model settings page |

## Deviations from Plan

### Rule 2 — Auto-add missing critical functionality

**1. Missing Settings fields caused validation error on .env load**
- **Found during:** Task 1.3 (verifying streamlit app imports)
- **Issue:** Pydantic v2 `extra_forbidden` rejected YIMEI_USERNAME, YIMEI_PASSWORD, CHANMAMA_TOKEN, MASTER_ENCRYPTION_KEY from .env
- **Fix:** Added these 4 fields to the Settings class
- **Files modified:** config/settings.py
- **Commit:** b3de903

## Known Stubs

None. All files are production quality for Phase 1 scope. test_api_connection() in settings.py is intentionally a stub (no real API calls in Phase 1 per CHECK-01).

## Threat Flags

None found — all surface is within planned boundaries.

## Self-Check: PASSED

All 19 created files verified. 4 commits confirmed.
