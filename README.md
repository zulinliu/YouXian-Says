# 攸县有话说 - 攸县方言短视频生产系统

用攸县方言讲活攸县故事。基于 AI 模型的自动化短视频生产系统，支持方言配音、数字人/模型占位、B-roll 视频合成和全流程 AI Agent 编排。

> **开源声明：** 本项目仅供学习参考，**商业使用需获得作者授权**。

## 项目状态

| 里程碑 | 阶段 | 需求完成度 | 测试覆盖 |
|--------|------|-----------|---------|
| **v1 MVP** | **全部 7 个阶段完成** | **56/56 v1 需求 ✓** | **66 个测试通过** |

## 快速开始

### 前置条件

- Python >= 3.11
- FFmpeg（推荐，视频合成必需）

### 一键安装

```bash
bash scripts/setup.sh
```

### 启动

```bash
# 1. 编辑环境变量（配置 API Key）
cp .env.example .env
vi .env

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 启动服务

# 启动 Streamlit 管理后台：
streamlit run web/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

# 或使用一键启动脚本：
bash run_ui.sh

# 4. 访问 http://localhost:8501
#    使用 .env 中配置的 ADMIN_PASSWORD 登录
```

### 已集成的真实 API

| 模型 | 用途 | 状态 |
|------|------|------|
| DeepSeek V4 Flash | 文本生成、选题发散、脚本创作 | ✅ 已配置 |
| GLM-5.1 | 深度推理、策略分析 | ✅ 已配置 |
| GPT-image-2 | 封面/场景/分镜图生成 | ✅ 已配置 |
| MiMo TTS (mimo-v2.5-tts) | 攸县方言语音合成 | ✅ 已配置 |

## 系统架构

```
./
├── config/                 # 系统配置与模型注册中心
│   ├── settings.py         # Pydantic Settings v2 配置管理
│   ├── model_registry.py   # 模型注册中心（6 个维度，35+ 模型选项）
│   └── prompts.py          # 6 个 Agent 提示词模板
├── services/               # 服务层
│   ├── llm.py              # LLM 统一调用（重试 + JSON 模式 + 多提供商）
│   ├── voice.py            # 语音合成（MiMo 主线 + 外部横评 + MiniMax 兜底）
│   ├── digital_human.py    # 数字人（7 种模式）
│   ├── video_gen.py        # B-roll 视频生成
│   ├── image_gen.py        # 图像生成（GPT-image-2 主线）
│   ├── composer.py         # FFmpeg 全自动合成管道
│   ├── publisher.py        # 多平台发布
│   └── model_logger.py     # 模型调用日志
├── agents/                 # AI Agent 编排层
│   ├── content_agent.py    # 内容 Agent（选题→脚本→分镜）
│   ├── production_agent.py # 制作 Agent（配音→数字人→B-roll→合成）
│   ├── ops_agent.py        # 运营 Agent（发布→数据→周报）
│   └── revision_parser.py  # 修改意见解析器
├── web/                    # 管理后台
│   ├── app.py              # FastAPI + Streamlit 组合入口
│   ├── auth.py             # 双认证（Streamlit 密码 + FastAPI JWT）
│   ├── database.py         # 异步 SQLite WAL 数据库
│   ├── models.py           # Pydantic 数据模型 + 14 状态状态机
│   ├── routers/            # 6 个 API 路由模块
│   └── pages/              # 5 个管理页面（选题/审核/发布/看板/设置）
├── scripts/                # 工具脚本
│   ├── setup.sh            # 一键安装
│   ├── init_db.py          # 数据库初始化（8 张表）
│   ├── build_knowledge.py  # 攸县知识库构建
│   ├── create_avatar.py    # 虚拟人设创建
│   ├── eval_models.py      # 模型横评工具
│   └── daily_run.py        # 每日自动流程
├── data/                   # 数据文件
│   ├── dialect_dict.json   # 方言俚语词典（20+ 条目）
│   ├── knowledge_base.md   # 攸县知识库（5 章节）
│   ├── persona.json        # 人设配置
│   └── voice_authorization.json # 声音授权管理
├── templates/branding/     # 品牌素材（片头/片尾/水印/BGM）
├── tests/                  # 测试用例
├── prd/                    # 产品需求/技术设计文档
│   ├── 2026-05-28-youxian-dialect-video-design.md   # 方言短视频设计方案
│   ├── 2026-05-28-youxian-tech-spec.md               # 技术方案说明书
│   └── 2026-05-28-model-agent-tool-optimization.md   # Agent 工具优化方案
├── .planning/              # 迭代过程文档
│   ├── PROJECT.md          # 项目概述
│   ├── REQUIREMENTS.md     # 需求列表
│   ├── ROADMAP.md          # 路线图
│   ├── STATE.md            # 项目状态追踪
│   └── phases/             # 各阶段规划与总结
└── output/                 # 输出目录（配音/B-roll/合成视频/评估结果）
```

## 阶段进展

| 阶段 | 目标 | 状态 | 完成日期 |
|------|------|------|---------|
| **Phase 1: Make It Run** | 项目骨架 + 全 Mock 管道，产出一条可审核视频 | ✅ **完成** | 2026-05-28 |
| **Phase 2: Core Platform** | FastAPI 后端 + SQLite + LLM 服务 + JWT 认证 | ✅ **完成** | 2026-05-28 |
| **Phase 3: Media Services** | 方言配音、数字人、B-roll、图像、发布服务 | ✅ **完成** | 2026-05-28 |
| **Phase 4: Agent Orchestration** | 内容/制作/运营 Agent + 修改意见解析器 | ✅ **完成** | 2026-05-28 |
| **Phase 5: Web Admin** | 完整 Streamlit 管理后台（5 个页面） | ✅ **完成** | 2026-05-28 |
| **Phase 6: Data & Knowledge** | 知识库、虚拟人设、模型横评、每日流程 | ✅ **完成** | 2026-05-29 |
| **Phase 7: Test & Acceptance** | 服务层测试 + 验收检查 | ✅ **完成** | 2026-05-29 |

## 验收项

| CHECK | 描述 | 状态 |
|-------|------|------|
| CHECK-01 | Mock 模式无需付费 API Key | ✅ |
| CHECK-02 | 模型连通性测试（Web 界面） | ✅ |
| CHECK-03 | 任务生命周期可追踪（idea→published） | ✅ |
| CHECK-04 | 发布默认确认优先（非无人值守） | ✅ |
| CHECK-05 | 声音授权管理 | ✅ |
| CHECK-06 | 事实风险分级标签 | ✅ |
| CHECK-07 | 模型调用日志记录 | ✅ |
| CHECK-08 | 周报支柱权重回写 | ✅ |

## 技术栈

| 类别 | 技术 |
|------|------|
| 运行时 | Python 3.11+、SQLite (WAL) |
| Web 框架 | FastAPI、Streamlit |
| 视频合成 | FFmpeg 6.1.1 |
| AI API | DeepSeek V4 Flash、GLM-5.1、GPT-image-2（DreamField 中转站） |
| 语音 API | MiMo V2.5 TTS（token-plan-cn） |
| 测试 | pytest 9.0.3、pytest-asyncio |
| 数据加密 | cryptography.fernet |
| 浏览器自动化 | Playwright |

## 测试

```bash
source venv/bin/activate
cd /home/liuzl/agent/YouXian-Says

# 运行所有测试（排除 API 和慢速测试）
pytest tests/ -q -m "not api and not slow"

# 运行全部测试
pytest tests/ -q
```

当前测试覆盖：**66 个测试通过** / 2 个 API 测试需配置 Key / 7 个慢速 FFmpeg 测试

## 安全说明

- **API Key 与隐私信息** 通过 `.env` 文件（已加入 `.gitignore`）配置，禁止提交到代码仓库
- `.env.example` 中仅包含 `sk-xxx` 等占位符，不包含真实密钥
- 加密后的模型参数存储于 `data/model_state.json`（已加入 `.gitignore`），不提交到仓库
- 提交代码前请确认无敏感信息泄露

## 许可

本项目开源，仅供学习参考。**商业使用需获得作者授权。**

本项目采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)（署名-非商业性使用-相同方式共享 4.0 国际）协议发布，详见 [LICENSE](./LICENSE) 文件：

- **您可以**：复制、分发、展示本作品，以及基于本作品创作衍生作品
- **限制**：
  - **非商业性使用** — 不得将本作品用于商业目的
  - **相同方式共享** — 衍生作品必须采用相同的许可协议
  - **署名** — 必须标注原作者信息
- **商业授权**：如需商业使用，请联系作者获取授权

Copyright © 2026 攸县有话说
