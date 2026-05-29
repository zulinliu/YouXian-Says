---
phase: phase6
plan: 06-01
subsystem: data-and-knowledge
tags: ["scripts", "voice-authorization", "fact-risk-tags", "pillar-weights", "knowledge-base", "persona", "model-eval", "daily-pipeline"]
dependency-graph:
  requires: ["phase5-web-admin"]
  provides: ["phase7-test-acceptance"]
  affects: ["content-agent", "ops-agent", "daily-operations"]
tech-stack:
  added: ["FFmpeg for avatar placeholder", "aiosqlite for DB checks"]
  patterns: ["CLI argparser", "idempotent build", "async daily pipeline"]
key-files:
  created:
    - scripts/build_knowledge.py
    - scripts/create_avatar.py
    - scripts/eval_models.py
    - scripts/daily_run.py
    - data/voice_authorization.json
  modified:
    - config/prompts.py
    - agents/content_agent.py
    - agents/ops_agent.py
decisions:
  - "Fact risk tags injected via prompt instruction (config/prompts.py) with default fallback in content_agent.py"
  - "Voice authorization stored as JSON data file, parsed at runtime by voice service (no separate authorization service)"
  - "Pillar weights parsed from weekly report LLM response, stored as _pillar_weights_parsed flag"
metrics:
  duration: "~5m"
  tasks: 6
  completed_date: "2026-05-29"
---

# Phase 6 Plan 01: Data and Knowledge Summary

**One-liner:** Data pipeline scripts (build_knowledge, create_avatar, eval_models, daily_run) + voice authorization enforcement + fact risk tag injection + weekly report pillar weight feedback.

## Verification Results

| Check | Status |
|-------|--------|
| 1. build_knowledge.py runs | PASS |
| 2. create_avatar.py runs | PASS |
| 3. eval_models.py runs (API gate) | PASS (auth gate, expected) |
| 4. daily_run.py runs | PASS |
| 5. Voice auth file exists with correct schema | PASS |
| 6. Fact risk tags in script_generation prompt | PASS |
| 7. pillar_weights in weekly report | PASS |
| 8. All existing tests pass (45/45) | PASS |

## Task Breakdown

### Task 1-4: Scripts Creation
Created 4 CLI scripts in `scripts/`:
- `build_knowledge.py` — Idempotent knowledge base builder from 5 sections (geography, food, customs, history, dialect) with source tags
- `create_avatar.py` — Virtual persona "YouYou" creator with FFmpeg avatar placeholder and mode flag
- `eval_models.py` — Async model evaluation across configured models (all calls fail gracefully without API keys)
- `daily_run.py` — Daily production pipeline checking pending scripts, publish queue, and collecting analytics data

### Task 5: Voice Authorization + Fact Risk Tags
- Created `data/voice_authorization.json` — Voice authorization policy (CHECK-05)
- Updated `config/prompts.py` — Added fact risk level instructions to `script_generation` prompt (CHECK-06)
- Updated `agents/content_agent.py` — Post-processing to ensure `fact_risk_level` on every script segment

### Task 6: Weekly Report Pillar Weights
- Updated `config/prompts.py` — Added `pillar_weights` instruction to `weekly_report` prompt (CHECK-08)
- Updated `agents/ops_agent.py` — Post-processing to extract and flag pillar weights from LLM response

## Deviations from Plan

None — plan executed exactly as written.

## Auth Gates

- **Task 3 (eval_models.py):** All 6 model evaluation calls returned auth gate errors (no API keys configured). This is expected behavior — the eval script fails gracefully and produces a partial results file.

## Self-Check: PASSED

- All 4 script files exist: PASS
- voice_authorization.json exists: PASS
- prompts.py fact_risk_level injection: PASS
- ops_agent.py pillar_weights extraction: PASS
- Commit hashes verified: 9a08a29, 83069ff
- 45/45 tests pass: PASS
