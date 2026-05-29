---
phase: phase2_core_platform
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - youxianduanshipin/web/database.py
  - youxianduanshipin/web/models.py
  - youxianduanshipin/web/auth.py
  - youxianduanshipin/web/routers/__init__.py
  - youxianduanshipin/web/routers/auth.py
  - youxianduanshipin/web/routers/topics.py
  - youxianduanshipin/web/routers/scripts.py
  - youxianduanshipin/web/routers/videos.py
  - youxianduanshipin/services/llm.py
  - youxianduanshipin/scripts/init_db.py
  - youxianduanshipin/web/app.py
  - youxianduanshipin/requirements.txt
  - youxianduanshipin/data/.gitkeep
autonomous: true
requirements:
  - DB-01
  - DB-02
  - DB-03
  - DB-04
  - DB-05
  - WEB-01
  - WEB-02
  - WEB-04
  - SVC-01
  - DATA-01
user_setup: []

must_haves:
  truths:
    - "User can run `python scripts/init_db.py` and see all 8 database tables created with WAL mode"
    - "User can start the FastAPI+Streamlit app and see login page"
    - "User can log into Streamlit with admin_password and access the app"
    - "User can POST /api/auth/token with correct password and receive a JWT"
    - "User can call LLMAbstract.chat() and LLMAbstract.chat_json() and get expected response types"
    - "User can list/create topics and scripts via API routes with valid JWT"
    - "Video status transitions are enforced: invalid transitions return error"
  artifacts:
    - path: "youxianduanshipin/web/database.py"
      provides: "Async SQLite connection with WAL mode"
      min_lines: 15
    - path: "youxianduanshipin/web/models.py"
      provides: "Pydantic request/response models"
      min_lines: 40
    - path: "youxianduanshipin/web/auth.py"
      provides: "Streamlit check_auth() + FastAPI JWT verify_token() using OAuth2PasswordBearer"
      min_lines: 40
    - path: "youxianduanshipin/web/routers/auth.py"
      provides: "POST /api/auth/token JWT issuance endpoint"
      min_lines: 30
    - path: "youxianduanshipin/web/routers/topics.py"
      provides: "Topics CRUD API"
      min_lines: 30
    - path: "youxianduanshipin/web/routers/scripts.py"
      provides: "Scripts CRUD API"
      min_lines: 30
    - path: "youxianduanshipin/web/routers/videos.py"
      provides: "Videos API with state machine enforcement"
      min_lines: 40
    - path: "youxianduanshipin/services/llm.py"
      provides: "LLMAbstract class with retry and JSON mode"
      min_lines: 60
    - path: "youxianduanshipin/scripts/init_db.py"
      provides: "Database initialization script creating all 8 tables with WAL mode"
      min_lines: 80
    - path: "youxianduanshipin/web/app.py"
      provides: "FastAPI + Streamlit combined entrypoint with lifespan"
      min_lines: 40
  key_links:
    - from: "web/database.py"
      to: "FastAPI lifespan in web/app.py"
      via: "import get_async_db; lifespan context manager"
      pattern: "lifespan|lifespan_context|get_async_db"
    - from: "web/auth.py"
      to: "web/routers/auth.py"
      via: "verify_token Depends import"
      pattern: "verify_token|login_for_access_token"
    - from: "services/llm.py"
      to: "config/model_registry.py"
      via: "ModelRegistry.snapshot()"
      pattern: "ModelRegistry\\.snapshot"
    - from: "scripts/init_db.py"
      to: "data/youxian.db"
      via: "sqlite3.connect(DB_PATH)"
      pattern: "sqlite3\\.connect.*youxian"

---

<objective>
实现 Phase 2 核心基础设施：FastAPI 异步后端 + SQLite WAL 模式数据库 + LLM 统一服务 + 双认证（Streamlit + FastAPI JWT）+ 数据库初始化脚本。

**Purpose:** 使攸县有话说平台具备持久化能力、API 基础和 LLM 统一调用层，为后续媒体服务和 Agent 编排提供平台基础。

**输出文件:** 见 files_modified 列出的所有文件。所有路径相对于 `youxianduanshipin/` 子目录。
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/phase2_core_platform/02-RESEARCH.md

<interfaces>
<!-- Key interfaces from existing code that this plan depends on -->

From config/settings.py:
- `settings.admin_password` — shared secret for both Streamlit login and JWT signing
- `settings.web_port` — port for streamlit run

From config/model_registry.py:
- `ModelRegistry.snapshot(function_id: str) -> ModelOption` — returns current active model config with resolved API key
- `ModelOption.resolved_api_key` — pre-resolved API key string
- `ModelOption.api_base` — base URL for API calls
- `ModelOption.model_name` — model identifier string
- `ModelOption.provider` — provider identifier (deepseek, minimax, openai_relay, etc.)

Existing web/app.py:
- Streamlit entrypoint with inline auth via `st.session_state.authenticated`
- Settings page import: `from web.pages.settings import render_settings_page`
- Uses `st.Page` + `st.navigation` for multi-page routing

Existing tests/conftest.py:
- `project_root` fixture returns `Path(__file__).parent.parent`
</interfaces>
</context>

<tasks>

<task type="auto">
<name>Task 1: Create web/database.py — Async SQLite connection with WAL mode</name>
<files>
youxianduanshipin/web/database.py
</files>
<action>
创建异步 SQLite 数据库连接模块，使用 aiosqlite (不是 sqlite3，sync sqlite3 会阻塞 FastAPI 事件循环)。

关键要求：
- 使用 `import aiosqlite`，数据库路径 `data/youxian.db`（相对于 youxianduanshipin/ 目录）
- 提供 `get_async_db()` 异步生成器，作为 FastAPI Depends，每次请求新建连接
- 设置 PRAGMA: `journal_mode=WAL`, `busy_timeout=5000`, `foreign_keys=ON`
- 设置 `row_factory = aiosqlite.Row` 使结果可 dict 化
- 使用 `DB_PATH` 模块级常量，通过 `os.path.join` 基于 `__file__` 计算绝对路径（这样可以支持从 any cwd 导入）

验证：文件存在，可被 `pytest` 导入且返回可工作连接。
</action>
<verify>
<automated>cd youxianduanshipin && python -c "import asyncio; from web.database import get_async_db; async def t(): async for db in get_async_db(): r=await db.execute('SELECT 1'); print(dict(await r.fetchone())); break; asyncio.run(t())"</automated>
</verify>
<done>
`get_async_db()` 异步生成器返回 aiosqlite 连接，WAL mode 已启用，row_factory 为 aiosqlite.Row，`SELECT 1` 返回 `{'1': 1}` 字典。
</done>
</task>

<task type="auto">
<name>Task 2: Create web/models.py — Pydantic request/response models</name>
<files>
youxianduanshipin/web/models.py
</files>
<action>
使用 Pydantic v2 创建 API 请求/响应模型。不需要 dataclass（RESEARCH.md 的 pydantic v2 方式）。

模型清单：
- `VideoStatus(str, Enum)` — 包含所有视频状态常量: idea, topic_selected, script_ready, storyboard_ready, voice_ready, avatar_ready, broll_ready, composing, composed, pending_review, approved, publishing, published, rejected
- `VALID_TRANSITIONS: dict[str, list[str]]` — 状态机允许转换字典（完整定义见 tech spec 7.2 或 RESEARCH.md Code Examples 的 VIDEO_STATUS_FLOW/VALID_TRANSITIONS）
- `VideoCreate(BaseModel)`: title (str), topic_id (int|None), script_id (int|None), storyboard_id (int|None), dialect_dictionary (str|None), fact_risk_level (str = "confirmed_fact")
- `VideoUpdate(BaseModel)`: status (str|None) — 用于状态转换
- `VideoResponse(BaseModel)`: id (int), title (str), status (str), topic_id (int|None), script_id (int|None), storyboard_id (int|None), dialect_dictionary (str|None), fact_risk_level (str), created_at (str), updated_at (str); model_config = {"from_attributes": True} 以便从数据库行转换
- `TopicCreate(BaseModel)`: video_id (int), title (str), pillar (str|None), source (str = "user")
- `TopicResponse(BaseModel)`: id (int), video_id (int), title (str), pillar (str|None), source (str), status (str), created_at (str); from_attributes = True
- `ScriptCreate(BaseModel)`: video_id (int), content (str), title (str|None), dialect_words (str|None)
- `ScriptResponse(BaseModel)`: id (int), video_id (int), content (str), title (str|None), dialect_words (str|None), status (str), fact_check_notes (str|None), created_at (str); from_attributes = True
- `StoryboardCreate(BaseModel)`: video_id (int), shots (str)
- `StoryboardResponse(BaseModel)`: id (int), video_id (int), shots (str), status (str), created_at (str); from_attributes = True
- `TokenResponse(BaseModel)`: access_token (str), token_type (str = "bearer")
- `ModelCallLogCreate(BaseModel)`: job_id (str), task_type (str), model_id (str), provider (str), channel (str), prompt_version (str|None), input_tokens (int = 0), output_tokens (int = 0), latency_ms (int = 0), cost_estimate (float = 0), success (int = 0), error_message (str|None), quality_score (float|None)
- `PublishQueueCreate(BaseModel)`: video_id (int), platform (str), scheduled_at (str|None)
- `AnalyticsDataCreate(BaseModel)`: video_id (int), platform (str), date (str), views (int = 0), likes (int = 0), comments (int = 0), shares (int = 0), followers (int = 0)

所有 BaseModel 使用 model_config = {"from_attributes": True} 支持从数据库行创建。
</action>
<verify>
<automated>cd youxianduanshipin && python -c "from web.models import VideoStatus, VideoCreate, VideoResponse, TopicCreate, ScriptCreate, TokenResponse, VALID_TRANSITIONS; assert VideoStatus.idea.value == 'idea'; assert len(VALID_TRANSITIONS) > 5"</automated>
</verify>
<done>
所有 Pydantic 模型可导入，枚举状态完整，状态转换字典包含所有 14 个状态的正确转换。
</done>
</task>

<task type="auto">
<name>Task 3: Create scripts/init_db.py — Database initialization script</name>
<files>
youxianduanshipin/scripts/init_db.py
youxianduanshipin/data/.gitkeep
</files>
<action>
创建数据库初始化脚本，使用 sync sqlite3（这是独立脚本，不在 FastAPI 事件循环中运行）。

使用 RESEARCH.md Pattern 5 的完整代码，需要从 RESEARCH.md 复制所有 CREATE TABLE 语句。重要提示：init_db.py 是**独立脚本**（同步 sqlite3 正确），不是 FastAPI 模块。

表结构（每个表必须包含 `CREATE TABLE IF NOT EXISTS`）：
1. **videos** — id, title, status, topic_id, script_id, storyboard_id, dialect_dictionary, fact_risk_level, created_at, updated_at; 外键关联 topics, scripts, storyboards
2. **topics** — id, video_id, title, pillar, source, status, created_at; 外键关联 videos
3. **scripts** — id, video_id, content, title, dialect_words, status, fact_check_notes, created_at; 外键关联 videos
4. **storyboards** — id, video_id, shots, status, created_at; 外键关联 videos
5. **model_call_logs** — id, job_id, task_type, model_id, provider, channel, prompt_version, input_tokens, output_tokens, latency_ms, cost_estimate, success, error_message, quality_score, created_at
6. **publish_queue** — id, video_id, platform, status, scheduled_at, published_at, platform_post_id, error_message, retry_count, created_at; 外键关联 videos
7. **analytics_data** — id, video_id, platform, date, views, likes, comments, shares, followers, collected_at; 外键关联 videos
8. **dialect_fixes** — id, original_text, fixed_text, context, source, created_at

要求：
- 使用 `os.path.dirname` 基于 `__file__` 计算 DB_PATH 绝对路径
- 创建 `data/` 目录如果不存在
- 连接后立即执行 PRAGMA WAL、busy_timeout=5000、foreign_keys=ON
- 所有 CREATE TABLE 使用 IF NOT EXISTS（幂等性）
- 打印成功消息和确认 WAL mode
- `if __name__ == "__main__"` 入口
- 创建空 `data/.gitkeep` 确保 data 目录被 git 跟踪

验证：运行脚本后检查数据库存在且表已创建。
</action>
<verify>
<automated>cd youxianduanshipin && python scripts/init_db.py && python -c "import sqlite3; c=sqlite3.connect('data/youxian.db'); c.row_factory=sqlite3.Row; tables=[r['name'] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]; assert 'videos' in tables; assert 'topics' in tables; assert 'scripts' in tables; assert 'storyboards' in tables; assert 'model_call_logs' in tables; assert 'publish_queue' in tables; assert 'analytics_data' in tables; assert 'dialect_fixes' in tables; print('All 8 tables created'); wal=c.execute('PRAGMA journal_mode').fetchone()[0]; print(f'WAL mode: {wal}')"