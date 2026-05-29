---
phase: phase2_core_platform
plan: 01
subsystem: database
tags: [database, sqlite, pydantic, schema]
requires: []
provides: [async-db-connection, pydantic-models, db-init-script]
affects: [web/database.py, web/models.py, scripts/init_db.py]
tech-stack:
  added: [aiosqlite]
  patterns: [async-generator-for-db-depends, pydantic-v2-from-attributes]
key-files:
  created:
    - web/database.py
    - web/models.py
    - scripts/init_db.py
  modified: []
decisions:
  - "aiosqlite for async SQLite (not sync sqlite3) to avoid blocking FastAPI event loop"
  - "DB_PATH computed from __file__ for cwd-independent imports"
  - "Pydantic response models use from_attributes=True for SQLite Row dict conversion"
  - "init_db.py uses sync sqlite3 (standalone script, not in event loop)"
metrics:
  duration: "5m"
  completed_date: "2026-05-28"
  tasks: 3
  commits: 3
---

# Phase 2 Plan 01: Database + Schema + Init — Summary

Database and schema layer for the YouXian Says platform: async SQLite connection with WAL mode, Pydantic API models, and database initialization script.

## Tasks

| # | Name | Status | Commit |
|---|------|--------|--------|
| 1 | Create web/database.py - Async SQLite WAL connection | done | 8f2c782 |
| 2 | Create web/models.py - Pydantic request/response models | done | 3b6df4a |
| 3 | Create scripts/init_db.py - Database initialization script | done | bc7cded |

### Task 1: web/database.py

Created async SQLite connection module with:
- `get_async_db()` — async generator for FastAPI `Depends`, opens per-request connections
- `get_db_connection()` — direct connection for standalone scripts
- PRAGMA: `journal_mode=WAL`, `busy_timeout=5000`, `foreign_keys=ON`
- `row_factory = aiosqlite.Row` for dict-like row access
- `DB_PATH` computed as absolute path from `__file__` (cwd-independent)

Verified: `SELECT 1` returns `{'1': 1}` via the async generator.

### Task 2: web/models.py

Created Pydantic v2 models:
- `VideoStatus` enum with all 14 video production states
- `VALID_TRANSITIONS` dict with full state machine (14 states, each with allowed transitions)
- Request models: `VideoCreate`, `VideoUpdate`, `VideoStatusUpdate`, `TopicCreate`, `ScriptCreate`, `StoryboardCreate`, `ModelCallLogCreate`, `PublishQueueCreate`, `AnalyticsDataCreate`
- Response models: `VideoResponse`, `TopicResponse`, `ScriptResponse`, `StoryboardResponse` (all with `from_attributes=True`)
- Auth model: `TokenResponse`

### Task 3: scripts/init_db.py

Created standalone database init script using sync sqlite3:
- 8 tables: `videos`, `topics`, `scripts`, `storyboards`, `model_call_logs`, `publish_queue`, `analytics_data`, `dialect_fixes`
- All foreign key relationships enforced
- `CREATE TABLE IF NOT EXISTS` for idempotency
- WAL mode confirmed: `wal`
- Data directory auto-created via `os.makedirs`

## Verification Results

```bash
# Task 1 - database connection
$ python -c "import asyncio; from web.database import get_async_db; ..."
{'1': 1}

# Task 2 - models
$ python -c "from web.models import VideoStatus, VALID_TRANSITIONS; ..."
All model assertions passed
VALID_TRANSITIONS has 14 entries

# Task 3 - init_db
$ python scripts/init_db.py && python -c "import sqlite3; ..."
Database initialized at .../data/youxian.db
Journal mode: wal
Tables created (8): analytics_data, dialect_fixes, model_call_logs, ...
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

All created files verified:
- PASS: web/database.py (36 lines, min 15)
- PASS: web/models.py (193 lines, min 40)
- PASS: scripts/init_db.py (149 lines, min 80)
- PASS: init_db creates all 8 tables + WAL mode
- PASS: get_async_db() returns working aiosqlite connection
- PASS: All models import and VALID_TRANSITIONS has 14 entries
- PASS: All 3 commits present in git log
