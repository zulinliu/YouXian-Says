---
gsd_state_version: 1.0
milestone: v2
milestone_name: Frontend Deep Refactor
status: in_progress
stopped_at: Frontend redesign complete — login, workspace, all 5 pages rebuilt
last_updated: "2026-05-29T09:30:00.000Z"
last_activity: 2026-05-29
progress:
  total_phases: 7
  completed_phases: 7
  v2_changes: 9 files modified, 2 files added, ~1100 lines changed
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-29)

**Core value:** 用攸县方言讲活攸县故事
**Current focus:** v2 前端深度重构完成 — 浅色设计系统 + 工作台 + 全站视觉升级

## Current Position

Phase: v2 Frontend Refactor
Status: ✅ **前端重构完成** — 待合并到 main
Last activity: 2026-05-29

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 14
- Average duration: ~12 min/plan
- Total execution time: ~2.5 hours (wall clock)
- Total test count: **66 passing / 2 API-marked / 7 slow-marked**

## Key Decisions (from all phases)

| Decision | Phase | Outcome |
|----------|-------|---------|
| Pydantic Settings v2 with SettingsConfigDict | 1 | ✓ Good |
| ModelRegistry with Fernet encrypted persistence | 1 | ✓ Good |
| Subprocess FFmpeg for complex filter chains | 1 | ✓ Good |
| aiosqlite for async SQLite (NOT sync sqlite3) | 2 | ✓ Good |
| PyJWT (NOT python-jose) for JWT auth | 2 | ✓ Good |
| FastAPI lifespan (NOT deprecated startup/shutdown) | 2 | ✓ Good |
| MiniMax as last-resort only, not default | 2 | ✓ Good |
| Strategy dispatch by model.id dict lookup | 3 | ✓ Good |
| Shared httpx client singleton | 3 | ✓ Good |
| Direct Python imports for page-to-agent calls | 5 | ✓ Good |
| Confirm-first publish mode (CHECK-04) | 5 | ✓ Good |
| Fact risk tags via prompt instruction | 6 | ✓ Good |
| Voice authorization JSON file | 6 | ✓ Good |
| MiMo TTS via chat/completions with api-key header | Integration | ✓ Good |
| GPT-image-2 via chat/completions (not responses) | Integration | ✓ Good |
| Env var resolution in ModelRegistry (${VAR}) | Integration | ✓ Good |

## Test Coverage Summary

| Area | Tests | Status |
|------|-------|--------|
| model_registry | 7 | ✅ Pass |
| mock_pipeline | 4 | ✅ Pass |
| voice service | 7 | ✅ Pass |
| image_gen service | 3 | ✅ Pass |
| digital_human service | 2 | ✅ Pass |
| video_gen service | 3 | ✅ Pass |
| publisher service | 4 | ✅ Pass |
| data files | 6 | ✅ Pass |
| web admin pages | 7 | ✅ Pass |
| agents | 5 | ✅ Pass |
| LLM service | 9 (2 marked api) | ✅ 7 + 2 api |
| composer | 11 (3 marked slow) | ✅ 8 + 3 slow |
| **Total** | **68** | **66 pass + 2 api** |

## Real API Integration Verified

| API | Status | Verified |
|-----|--------|----------|
| DeepSeek V4 Flash (DreamField relay) | ✅ | Topic divergence, script generation |
| GLM-5.1 (DreamField relay) | ✅ | Text completion |
| GPT-image-2 (DreamField relay, chat/completions) | ✅ | 881KB image generated |
| MiMo TTS (token-plan, mimo-v2.5-tts) | ✅ | 207KB WAV audio generated |

## Deferred Items

Items acknowledged for v2 planning:

| Category | Item | Priority |
|----------|------|----------|
| Platform | Douyin/Kuaishou official API real integration | High |
| Platform | WeChat/Xiaohongshu Playwright publish flow | High |
| Voice | MiMo VoiceClone reference audio upload | High |
| Voice | CosyVoice 3.0 deployment for dialect TTS | Medium |
| Digital Human | HeyGen/Tavus purchase + real API | Medium |
| B-roll | Runway/Veo/Kling purchase + real API | Medium |
| Data | Real analytics data collection | Medium |
| Auto | Cron-based daily pipeline deployment | Medium |
| Auto | Unattended publish mode (gated) | Low |
| Platform | Kuaishou/Xiaohongshu/Bilibili expansion | Low |

## v1 Requirement Status

- Total v1 requirements: **56**
- Complete: **56**
- Pending: **0**
- Coverage: **100% ✓**

## Session Continuity

Last session: 2026-05-29T08:30:00.000Z
Stopped at: v1 MVP Complete — Ready for v2 planning
