# YouXian Says — 攸县有话说

## What This Is

一个以攸县方言为核心特色的 AI 短视频内容生产系统。通过 AI Agent 全流程自主执行（选题共创 → 脚本创作 → 分镜设计 → 视听制作 → 后期合成 → 多平台发布 → 数据闭环），让个人独立运营的团队能够每周稳定输出 3 条攸县方言短视频，覆盖抖音和视频号。

**v1 MVP 已完成。** 7 个阶段全部交付，56/56 需求实现，66 个测试通过。真实 API（DeepSeek V4 Flash、GLM-5.1、GPT-image-2、MiMo TTS）已集成并可运行。

## Core Value

**用攸县方言讲活攸县故事。** 一切决策以"能否持续稳定产出地道的攸县方言短视频"为最高优先级。如果系统不能每周产出 3 条可发布的视频，其他功能皆无意义。

## Requirements

### Validated

- ✓ **PROJ-01**: 项目目录结构搭建和配置文件（settings.py, model_registry.py, prompts.py, .env.example, requirements.txt, setup.sh） — Phase 1
- ✓ **PROJ-02**: 模型注册中心（可视化 Web 切换模型、编辑 API 参数、测试连接） — Phase 1
- ✓ **PROJ-03**: 内容 Agent 实现（选题共创 → 脚本生成 → 分镜设计） — Phase 4
- ✓ **PROJ-04**: 制作 Agent 实现（方言配音 → 数字人/B-roll → 视频合成） — Phase 4
- ✓ **PROJ-05**: 运营 Agent 实现（发布调度 → 数据采集 → 周报分析） — Phase 4
- ✓ **PROJ-06**: 方言配音服务（MiMo 主线 + 外部语音横评 + MiniMax 兜底） — Phase 3
- ✓ **PROJ-07**: 数字人/Mock 模式（mock/local/manual/heygen 四种模式） — Phase 3
- ✓ **PROJ-08**: 视频 B-roll 生成服务（mock/local/runway/veo/kling/luma/pika/hailuo 多种模式） — Phase 3
- ✓ **PROJ-09**: GPT-image-2 图像生成主线（封面/分镜参考/场景） — Phase 3
- ✓ **PROJ-10**: FFmpeg 视频合成服务（数字人+配音+B-roll+字幕+背景音乐+品牌元素） — Phase 1
- ✓ **PROJ-11**: 多平台发布（抖音/快手 API + 视频号/小红书 Playwright） — Phase 3
- ✓ **PROJ-12**: Streamlit Web 管理后台（选题共创/审核中心/发布管理/数据看板/模型设置） — Phase 5
- ✓ **PROJ-13**: FastAPI 后端 + SQLite 数据库（WAL 模式 + 任务状态机） — Phase 2
- ✓ **PROJ-14**: 初始化脚本（数据库初始化、知识库构建、声音克隆配置、模型横评工具） — Phase 6
- ✓ **PROJ-15**: Mock 模式全流程跑通（不依赖任何付费 API 即可生成可审核成片） — Phase 1
- ✓ **PROJ-16**: 攸县方言知识库（方言俚语词典、攸县知识库） — Phase 3
- ✓ **PROJ-17**: 技术评审验收项：全部 8 项 CHECK 已通过 — Phase 7

### Active

v1 MVP 已完成。v2 规划中。

### Out of Scope

- **四平台日更（快手/小红书/B站）** — MVP 先做每周 3 条，仅抖音和视频号。稳定后再扩展。
- **真人数字人形象授权** — MVP 先虚拟本地人设，真人授权进入第二阶段。
- **多声音授权** — 默认仅本人声音可用于生产；其他人声音必须有明确授权记录才扩展。
- **HeyGen/Runway 采购** — 搭建期不强依赖付费服务，先做 mock 模式跑通全流程。
- **无人值守自动发布** — MVP 默认所有发布进入待确认队列，不允许直接自动发布。
- **本地 GPU 训练** — 无 GPU 资源，不采用本地语音/视频模型训练路线。
- **n8n 工作流引擎** — 系统初期以 Agent 自主调度为主，n8n 作为可选增强。

## Context

- 项目基于 2026-05-28 评审通过的三份设计文档
- 版本迭代统一使用 `feat/vX.Y.Z` 分支；完成后通过 PR 合入 `main` 并发布 `vX.Y.Z` 发行版
- 项目为个人独立操作，MVP 约 40-70 分钟/周用户投入
- 方言声音使用 MiMo V2.5 TTS（通过 token-plan-cn 调用 chat/completions 端点）
- 文本/图像模型通过 DreamField 中转站调用（DeepSeek V4 Flash、GLM-5.1、GPT-image-2）
- 数字人/B-roll 在采购前使用 mock/local/manual 模式占位
- MiniMax 全系列模型仅作为基线/兜底，不进入主链路
- 模型调用通过 New API 中转站兼容通道（标记为 channel=new_api_relay）

## Constraints

- **技术栈**: Python 3.11+、FastAPI、Streamlit、SQLite、FFmpeg、Playwright
- **团队**: 个人独立操作，所有流程需 Agent 自动化
- **算力**: 无本地 GPU，所有生成能力依赖 API 调用
- **覆盖**: MVP 仅覆盖抖音和视频号（9:16），每周 3 条
- **预算**: 搭建期不采购 HeyGen/Runway 等媒体生成服务
- **数据安全**: 账号凭证、Cookie、API Key 不传入生成模型

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AI Agent 全流程自主 | 个人独立操作，无法人工参与每个环节 | ✓ Good |
| MiniMax 全系降级为基线/兜底 | 用户实测效果相对不高 | ✓ Good |
| 中转站标记为 new_api_relay 可进主链路 | 用户说明效果接近官方，但需单独监控 | ✓ Good |
| 深度推理顺序 GLM-5.1 → GPT-5.5 → DeepSeek V4 Pro | 按用户指定 | ✓ Good |
| 图像生产主线 GPT-image-2 | 用户实测该模型效果最好 | ✓ Good |
| 语音主线 MiMo VoiceClone/TTS | 已购小米语音能力 | ✓ Good |
| MiMo TTS 走 chat/completions + api-key header | 实际 API 测试验证 | ✓ Good |
| GPT-image-2 走 chat/completions 非 responses | 中转站不支持 responses 端点 | ✓ Good |
| 版本分支统一使用 `feat/vX.Y.Z` | 版本分支完成后 PR 合入 `main` 并发布同版本发行版；历史 `feat/v1`/`feat/v2` 迁移为语义化版本分支 | ✓ Good |

## v2 规划方向

| 优先级 | 项目 | 说明 |
|--------|------|------|
| P0 | 抖音/视频号正式发布接入 | 官方 API + Playwright 真实发布流程 |
| P0 | MiMo VoiceClone 参考音频上传 + 本人声音克隆 | 正式接入声音克隆 |
| P1 | HeyGen 小额购买 + 真实数字人口播验证 | 替换 mock 数字人 |
| P1 | CosyVoice 3.0 方言 TTS 部署 | 更地道的攸县话配音 |
| P2 | 日更自动化部署（cron + n8n） | 实现每日自动执行 |
| P2 | 数据看板联接通告数据源 | 蝉妈妈/飞瓜数据接入 |
| P3 | 四平台扩展 + 无人值守发布 | 达到条件后开启 |

## Branching & Release Memory

- **永久约定**：正式版本迭代分支统一命名为 `feat/vX.Y.Z`，例如 `feat/v0.1.0`、`feat/v0.2.0`、`feat/v1.2.0`。
- **主干规则**：`main` 是唯一稳定发布线；版本分支完成验收后，通过 PR 合入 `main`。
- **发行规则**：PR 合入 `main` 后发布同版本发行版，tag 格式为 `vX.Y.Z`，并保持 `pyproject.toml`、`CHANGELOG.md`、Git tag 一致。
- **迁出规则**：发行完成后，从最新 `main` 迁出下一版本分支。
- **历史迁移**：`feat/v1` → `feat/v1.0.0`，`feat/v2` → `feat/v1.1.0`，`feature/liuzl` → `archive/feature-liuzl`；下一版本分支为 `feat/v1.2.0`。
- **详细规范**：见 `docs/BRANCHING_AND_RELEASE.md`。

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? �� Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-06 after branch/release management standardization*
