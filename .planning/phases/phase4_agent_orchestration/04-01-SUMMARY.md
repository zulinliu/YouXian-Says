# Phase 4 Plan 01: Agent Orchestration Summary

**Objective:** Create the agent orchestration layer (ContentAgent, ProductionAgent, OpsAgent,
RevisionParser) that coordinates LLM, media, and publishing services.

**Status:** COMPLETE — 27 tests passing (22 existing + 5 new agent tests)

---

## Files Created / Modified

| File | Status | Description |
|------|--------|-------------|
| `youxianduanshipin/agents/__init__.py` | Created | Package init, exports all agents |
| `youxianduanshipin/agents/content_agent.py` | Created | ContentAgent — topic diverge, script gen, storyboard |
| `youxianduanshipin/agents/production_agent.py` | Created | ProductionAgent — voice DH b-roll compose pipeline |
| `youxianduanshipin/agents/ops_agent.py` | Created | OpsAgent — publish, data collection, weekly report |
| `youxianduanshipin/agents/revision_parser.py` | Created | Parse NL feedback to structured actions |
| `youxianduanshipin/config/prompts.py` | Modified | Added 5 agent-specific prompts |
| `youxianduanshipin/data/__init__.py` | Created | Loads DIALECT_DICT and KNOWLEDGE_BASE at import |
| `youxianduanshipin/tests/test_agents/__init__.py` | Created | Empty package init |
| `youxianduanshipin/tests/test_agents/conftest.py` | Created | Shared fixtures (mock_dialect_dict, sample_topic, sample_script) |
| `youxianduanshipin/tests/test_agents/test_content_agent.py` | Created | 3 tests for ContentAgent structure |
| `youxianduanshipin/tests/test_agents/test_revision_parser.py` | Created | 2 tests for parse_revision (mocked LLM) |

## Architecture

```
Agents (orchestrators, pure coordination)
  |
  +-- ContentAgent       → LLMAbstract.chat_json() for diverge → script → storyboard
  |                        generates reference images via image_gen service
  |
  +-- ProductionAgent    → voice → digital_human → broll(parallel) → compose(to_thread)
  |                        sync FFmpeg wrapped in asyncio.to_thread()
  |
  +-- OpsAgent           → publisher.publish() → data collection → LLM weekly report
  |                        publish_approved wraps publish(video_path, meta, platforms)
  |
  +-- RevisionParser     → NL text → structured action list (via LLM)

Key patterns:
- All agents use ModelRegistry.snapshot() for runtime isolation
- All LLM calls log via model_logger.log_model_call()
- No agents own state — they coordinate services
```

## Deviations from Plan

### Rule 2 — Missing critical functionality

**1. OpsAgent.publish_approved() had wrong function signature**
- **Found during:** Verification (import test failed)
- **Issue:** The `publish` function in `services/publisher.py` accepts `(video_path, meta, platforms, job_id)` — the plan's template used keyword args `(title=, tags=, description=)` that don't exist in the actual `publish()` signature
- **Fix:** Created `meta` dict to wrap title/tags/description and pass as single `meta` parameter
- **Commit:** `de6df5c`

### Rule 1 — Auto-fix bugs

**1. Revision parser tests called real LLM**
- **Found during:** Test run (failed with Missing credentials error)
- **Issue:** The test called `parse_revision()` which internally calls `text_llm.chat_json()` — without API keys configured, this raises OpenAIError
- **Fix:** Patched `agents.revision_parser.text_llm` with `AsyncMock` in both tests
- **Commit:** `de6df5c`

## Verification Results

```
All agents importable          ✓
ContentAgent structure         ✓ (diverge_topics, generate_script, generate_storyboard, run_creative_session)
Prompts (6 total)              ✓ (36-284 chars each)
Data loading                   ✓ (23 DIALECT_DICT entries, 2234 KB chars)
Agent tests (5)                ✓ (passed)
All 27 project tests           ✓ (passed — no regressions)
```

## Commits

| Hash | Message |
|------|---------|
| `3159ed0` | feat(phase4): create agents package init with exporter imports |
| `f2b0bb7` | feat(phase4): create ContentAgent, ProductionAgent, OpsAgent, and RevisionParser |
| `a28bed5` | feat(phase4): add agent-specific prompts to config/prompts.py |
| `fa179a7` | feat(phase4): create data/__init__.py with DIALECT_DICT and KNOWLEDGE_BASE loading |
| `49678b0` | feat(phase4): add agent tests with fixtures for ContentAgent and RevisionParser |
| `de6df5c` | fix(phase4): mock LLM calls in revision_parser tests and fix OpsAgent publish signature |

## Self-Check: PASSED

All 11 files verified existing on disk. All 6 commit hashes verified in git history. 27 tests passing.
