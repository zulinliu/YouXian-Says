---
phase: phase2_core_platform
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - services/llm.py
  - web/auth.py
  - web/routers/__init__.py
  - web/routers/auth.py
  - web/routers/topics.py
  - web/routers/scripts.py
  - web/routers/videos.py
  - web/app.py
  - requirements.txt
  - data/.gitkeep
autonomous: true
requirements:
  - DB-01
  - DB-02
  - WEB-02
  - WEB-04
  - SVC-01
user_setup: []

must_haves:
  truths:
    - "User can POST /api/auth/token and get JWT access_token back"
    - "User can call protected API routes (GET /api/topics, GET /api/scripts, GET /api/videos) with valid JWT and get DB data"
    - "User can POST /api/videos and status transitions are validated against allowed transitions"
    - "User can POST /api/auth/token with wrong password and get 401"
    - "Calling a protected route without a token returns 401"
    - "LLM service is importable and ModelRegistry snapshot routing works"
    - "FastAPI app starts with lifespan context manager and serves both Streamlit and API"
  artifacts:
    - path: "services/llm.py"
      provides: "LLMAbstract class with chat, chat_json, retry"
      exports:
        - "LLMAbstract"
        - "text_llm"
        - "multimodal_llm"
      min_lines: 60
    - path: "web/auth.py"
      provides: "Streamlit check_auth() + FastAPI verify_token() + FastAPI login_for_access_token()"
      exports:
        - "check_auth"
        - "verify_token"
        - "oauth2_scheme"
      min_lines: 60
    - path: "web/routers/__init__.py"
      provides: "Router package init"
      min_lines: 1
    - path: "web/routers/auth.py"
      provides: "POST /api/auth/token endpoint"
      exports:
        - "router"
      min_lines: 30
    - path: "web/routers/topics.py"
      provides: "Topics CRUD endpoints"
      exports:
        - "router"
      min_lines: 50
    - path: "web/routers/scripts.py"
      provides: "Scripts CRUD endpoints"
      exports:
        - "router"
      min_lines: 50
    - path: "web/routers/videos.py"
      provides: "Videos API with state machine enforcement"
      exports:
        - "router"
      min_lines: 60
    - path: "web/app.py"
      provides: "Combined FastAPI + Streamlit entrypoint"
      min_lines: 50
  key_links:
    - from: "web/auth.py"
      to: "config/settings.py"
      via: "settings.admin_password"
      pattern: "settings\\.admin_password"
    - from: "services/llm.py"
      to: "config/model_registry.py"
      via: "ModelRegistry.snapshot()"
      pattern: "ModelRegistry\\.snapshot"
    - from: "web/app.py"
      to: "web/database.py"
      via: "lifespan context manager"
      pattern: "lifespan|lifespan_context"

---

<objective>
实现 LLM 统一服务层、FastAPI JWT 认证、API 路由和 FastAPI+Streamlit 组合入口。本计划与 Plan 01 并行（Wave 1），二者无文件冲突。

**Purpose:** 提供 LLM 统一调用层（含重试和 JSON 模式）、JWT 保护 API 路由（认证/选题/脚本/视频 CRUD + 状态机）和组合服务入口点。

**输出文件:** 见 files_modified 列表。所有路径相对于 `` 子目录。
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
<!-- Interfaces this plan consumes from existing codebase -->

From config/settings.py:
- `settings.admin_password` — str, shared secret for Streamlit login + JWT signing
- Singleton: `settings = Settings()` — use `from config.settings import settings`

From config/model_registry.py:
- `ModelRegistry.snapshot(function_id: str) -> ModelOption`
- `ModelOption.resolved_api_key: str`
- `ModelOption.api_base: str`
- `ModelOption.api_compatibility: str` (e.g. "openai_chat")
- `ModelOption.supports_json: bool`

From web/database.py (created by Plan 01, Wave 1):
- `get_async_db()` -> async generator yielding aiosqlite connection
- `DB_PATH: str` — absolute path to database

From web/models.py (created by Plan 01, Wave 1):
- `VALID_TRANSITIONS: dict[str, list[str]]`
- `VideoStatus` enum
- `VideoCreate`, `VideoResponse`, `VideoUpdate` BaseModel
- `TopicCreate`, `TopicResponse` BaseModel
- `ScriptCreate`, `ScriptResponse` BaseModel
- `StoryboardCreate`, `StoryboardResponse` BaseModel
- `TokenResponse` BaseModel

From existing web/app.py:
- Current Streamlit-only entrypoint with inline auth, settings page navigation

From existing tests/conftest.py:
- `project_root` fixture
</interfaces>
</context>

<tasks>

<task type="auto">
<name>Task 1: Create services/llm.py — LLMAbstract unified service with retry and JSON mode</name>
<files>
services/llm.py
</files>
<action>
创建 LLM 统一调用服务。遵循 RESEARCH.md Pattern 4 的代码（使用 ModelRegistry.snapshot 进行模型路由，不使用硬编码配置）。

关键设计：
- `LLMAbstract` 类接受 `function_id: str = "text_llm"` 参数
- `_get_client()` 方法: 调用 `ModelRegistry.snapshot(self.function_id)` 获取当前激活模型配置，使用 `model.resolved_api_key` 和 `model.api_base` 构造 `openai.AsyncOpenAI` 客户端
  - 所有 provider 统一使用 `openai.AsyncOpenAI`（因为 DeepSeek、OpenAI Relay、GLM Relay 等都兼容 OpenAI 格式；Minimax 等非 OpenAI 兼容 provider 在 Phase 3 处理）
  - 不需要 provider 分支（简化 Phase 2，Phase 3 再添加非 OpenAI 兼容 provider）
- `chat()` 方法:
  - 使用 `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30), retry=retry_if_exception_type((ConnectionError, TimeoutError)))` 装饰
  - 调用 `client.chat.completions.create(model=model_name, messages=messages, **kwargs)`
  - 返回 `response.choices[0].message.content` (str)
- `chat_json()` 方法:
  - 调用 `self.chat()` 并传入 `response_format={"type": "json_object"}`
  - 用 `json.loads(content)` 解析返回 dict
  - 捕获 `json.JSONDecodeError` 并记录到日志
- 模块级全局实例：`text_llm = LLMAbstract("text_llm")` 和 `multimodal_llm = LLMAbstract("multimodal")`

关于 mermaid/可视化标志：tech spec 使用的是 `mermaid` 互斥标签（"text", "tool", "image", "video", "audio", "avatar" 而在 model_registry.py 中实际上是"modalities"），这与 Phase 2 的 LLM 服务无关。仅处理 `openai.AsyncOpenAI` 客户端创建。

注意：mermaid 相关代码不涉及 LLM 服务，忽略之。

关于 `@retry` 装饰器的参数：注意 `retry_if_exception_type` 是 tenacity 的正确定义方式（不是 `retry_on_exception` 等旧写法）。

不要创建 tests/ 文件（Plan 03 负责测试）。

需要将 `aiosqlite>=0.20.0` 和 `pyjwt>=2.8.0` 添加到 requirements.txt（如果尚未存在）。
</action>
<verify>
<automated>python -c "from services.llm import LLMAbstract, text_llm, multimodal_llm; assert isinstance(text_llm, LLMAbstract); assert text_llm.function_id == 'text_llm'; assert multimodal_llm.function_id == 'multimodal'"