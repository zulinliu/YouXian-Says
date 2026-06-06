# Roadmap: YouXian Says (攸县有话说)

## Overview

从项目骨架到可交付的攸县方言短视频 AI 生产系统。采用垂直 MVP 模式，每个阶段交付端到端的可验证能力。第一阶段即可通过全 Mock 模式跑通视频生产管道，后续逐步替换为真实 AI 服务、Agent 编排、Web 管理后台，最终完成测试验收。

## Phases

- [x] **Phase 1: Make It Run** — 项目骨架 + 全 Mock 管道，跑通第一条可审核视频
- [x] **Phase 2: Core Platform** — 数据库 + FastAPI 后端 + LLM 服务，构建基础平台
- [x] **Phase 3: Media Services** — 方言配音、数字人、B-roll、图像生成、发布服务
- [x] **Phase 4: Agent Orchestration** — 内容/制作/运营 Agent + 修改意见解析器
- [x] **Phase 5: Web Admin** — Streamlit 管理后台完整功能
- [x] **Phase 6: Data & Knowledge** — 知识库构建、初始化脚本、治理验收
- [x] **Phase 7: Test & Acceptance** — 服务层测试 + 剩余验收项

## Phase Details

### Phase 1: Make It Run
**Goal**: 搭建完整项目目录结构，通过全 Mock 模式跑通从配置到视频合成的完整管道，产出第一条可审核的攸县方言短视频
**Mode**: mvp
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07, SVC-06, DATA-08, TEST-01, TEST-06, CHECK-01
**Success Criteria** (what must be TRUE):
  1. User can run `setup.sh` and have a working project environment with all dependencies ✓
  2. Models configurable via model_registry.py ✓
  3. Full mock pipeline produces a playable video file ✓
  4. Video includes: mock digital human, mock B-roll, mock voiceover, subtitles, branding, BGM ✓
  5. `pytest tests/test_model_registry.py` passes ✓

Plans:
- [x] Plan 01: Project skeleton + config (settings.py, model_registry.py, prompts.py, .env, setup.sh)
- [x] Plan 02: Mock pipeline (composer.py, branding templates, SRT generation)
- [x] Plan 04: Tests (model_registry + mock pipeline)

### Phase 2: Core Platform
**Goal**: 搭建 FastAPI 后端 + SQLite 数据库（WAL 模式），实现 LLM 统一调用层、Streamlit 登录认证和数据库初始化脚本，使平台具备持久化能力和 API 基础
**Mode**: mvp
**Depends on**: Phase 1
**Requirements**: DB-01~05, WEB-01, WEB-02, WEB-04, SVC-01, DATA-01
**Success Criteria** (what must be TRUE):
  1. User can run `scripts/init_db.py` and have all 8 database tables created ✓
  2. User can start the FastAPI server and access API routes with JWT authentication ✓
  3. User can call the LLM service with any configured model and receive a structured JSON response ✓
  4. User can log in to Streamlit with credentials and have session state maintained ✓
  5. Database tables support full task state machine for video production workflow ✓

Plans:
- [x] Plan 01: Database schema, connection, models, init script
- [x] Plan 02: LLM service, JWT auth, API routes, combined entrypoint
- [x] Plan 03: Tests (database, auth, LLM service)

### Phase 3: Media Services
**Goal**: 实现全部媒体生成服务和多平台发布能力
**Mode**: mvp
**Depends on**: Phase 2
**Requirements**: SVC-02~05, SVC-07, DATA-06, DATA-07, CHECK-07
**Success Criteria** (what must be TRUE):
  1. `voice.generate()` produces WAV via MiMo VoiceClone (or mock fallback) ✓
  2. `digital_human.create()` produces MP4 for mock/local/manual modes ✓
  3. `video_gen.generate_broll()` produces MP4 for mock mode ✓
  4. `image_gen.generate()` produces image via GPT-image-2 relay (or mock) ✓
  5. `publisher.publish()` returns result for all 4 platforms ✓
  6. All model calls logged to `model_call_logs` table ✓
  7. `data/dialect_dict.json` exists with 20+ entries ✓
  8. `data/knowledge_base.md` exists with 5 topic sections ✓

Plans:
- [x] Plan 01: All services + data files + tests (22 tests)

### Phase 4: Agent Orchestration
**Goal**: 实现全流程 AI Agent
**Mode**: mvp
**Depends on**: Phase 2, Phase 3
**Requirements**: AGENT-01~04, TEST-05
**Success Criteria** (what must be TRUE):
  1. ContentAgent diverges topics via LLM, generates scripts with dialect injection and storyboards ✓
  2. ProductionAgent orchestrates voice → digital human → b-roll → compose ✓
  3. OpsAgent publishes, collects data, generates weekly report ✓
  4. RevisionParser parses natural language feedback into structured operations ✓
  5. All agents use ModelRegistry.snapshot() at task start ✓
  6. All agent operations logged via model_logger.log_model_call() ✓
  7. Agent tests pass: pytest tests/test_agents/ -x -v ✓

Plans:
- [x] Plan 01: All agents (ContentAgent, ProductionAgent, OpsAgent, RevisionParser) + tests

### Phase 5: Web Admin
**Goal**: 完成 Streamlit 管理后台全部页面
**Mode**: mvp
**Depends on**: Phase 4
**Requirements**: WEB-03, WEB-05~09, CHECK-03, CHECK-04
**Success Criteria** (what must be TRUE):
  1. User can create topic on Create page, see AI-generated options, confirm ✓
  2. User can preview storyboard and video in Review center, approve/reject ✓
  3. User can see pending publish queue, select platforms, schedule — confirm-first mode ✓
  4. User can view analytics dashboard with trends and weekly report ✓
  5. User can view any video task's full lifecycle and retry any failed stage ✓

Plans:
- [x] Plan 01: All 5 admin pages + lifecycle tracking + confirm-first publish

### Phase 6: Data & Knowledge
**Goal**: 完成知识库构建、虚拟人设、模型横评、每日流程、治理验收
**Mode**: mvp
**Depends on**: Phase 5
**Requirements**: DATA-02~05, CHECK-05, CHECK-06, CHECK-08
**Success Criteria** (what must be TRUE):
  1. User can run `scripts/build_knowledge.py` to build knowledge base ✓
  2. User can run `scripts/create_avatar.py` to create virtual persona ✓
  3. User can run `scripts/eval_models.py` with 70+ samples ✓
  4. User can run `scripts/daily_run.py` for daily pipeline ✓
  5. Weekly report writes back content pillar weights ✓
  6. Fact risk tags on every script ✓
  7. Voice authorization enforcement ✓

Plans:
- [x] Plan 01: All data scripts + governance + pillar weights

### Phase 7: Test & Acceptance
**Goal**: 完成服务层测试（LLM、Voice、Composer）和验收项（模型连通性测试）
**Mode**: mvp
**Depends on**: Phase 6
**Requirements**: TEST-02~04, CHECK-02
**Success Criteria** (what must be TRUE):
  1. `pytest tests/test_services/test_llm.py` passes ✓
  2. `pytest tests/test_services/test_voice.py` passes ✓
  3. `pytest tests/test_services/test_composer.py` passes ✓
  4. User can edit API Base/Key/Name and click "Test Connection" ✓

Plans:
- [x] Plan 01: Remaining tests + test_api_connection enhancement

## Progress

**Execution Order:** Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Status | Completed |
|-------|--------|-----------|
| 1. Make It Run | ✅ Complete | 2026-05-28 |
| 2. Core Platform | ✅ Complete | 2026-05-28 |
| 3. Media Services | ✅ Complete | 2026-05-28 |
| 4. Agent Orchestration | ✅ Complete | 2026-05-28 |
| 5. Web Admin | ✅ Complete | 2026-05-28 |
| 6. Data & Knowledge | ✅ Complete | 2026-05-29 |
| 7. Test & Acceptance | ✅ Complete | 2026-05-29 |

**Complete!** All 56 v1 requirements verified. Ready for v2 planning.


## Version Branch & Release Plan

- `feat/v1.0.0`：v1 MVP 完成分支，对应发行版 `v1.0.0`。
- `feat/v1.1.0`：前端深度重构 + 分支发行规范，对应待发布发行版 `v1.1.0`。
- `feat/v1.2.0`：下一版本迭代分支，从 `v1.1.0` 合入/发布后的最新 `main` 迁出。
- 分支、PR、Release 详细规则见 `docs/BRANCHING_AND_RELEASE.md`。
