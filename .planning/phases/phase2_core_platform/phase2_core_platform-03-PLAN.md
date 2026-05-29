---
phase: phase2_core_platform
plan: 03
type: tdd
wave: 2
depends_on:
  - 01
  - 02
files_modified:
  - tests/conftest.py
  - tests/test_database.py
  - tests/test_auth.py
  - tests/test_llm.py
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
    - "pytest tests/test_database.py passes: init_db, schema, WAL mode, state machine, inserts"
    - "pytest tests/test_auth.py passes: Streamlit login, JWT token creation/verification, invalid token rejection"
    - "pytest tests/test_llm.py passes: chat method, chat_json, retry decorator, model routing"
    - "All test files have proper fixtures and use monkeypatch.setenv() for admin_password"
  artifacts:
    - path: "tests/conftest.py"
      provides: "Updated shared test fixtures (temp db, test settings)"
      exports:
        - "test_db_path"
        - "async_test_db"
      min_lines: 50
    - path: "tests/test_database.py"
      provides: "Database tests covering init, WAL, state machine, inserts"
      min_lines: 80
    - path: "tests/test_auth.py"
      provides: "Auth tests covering Streamlit login, JWT, token validation"
      min_lines: 80
    - path: "tests/test_llm.py"
      provides: "LLM service tests covering chat, chat_json, retry, routing"
      min_lines: 80
  key_links:
    - from: "tests/conftest.py"
      to: "scripts/init_db.py"
      via: "import init_database function"
      pattern: "init_database|init_db"
    - from: "tests/test_auth.py"
      to: "web/auth.py"
      via: "import verify_token, check_auth"
      pattern: "verify_token|check_auth"
    - from: "tests/test_llm.py"
      to: "services/llm.py"
      via: "import LLMAbstract"
      pattern: "LLMAbstract|text_llm"

---

<objective>
为 Phase 2 创建完整的测试套件：数据库测试、认证测试、LLM 服务测试。采用 TDD 方法，先定义期望行为再验证实现。

**Purpose:** 确保 Phase 2 所有功能（DB、Auth、LLM）都有自动化测试覆盖，防止回归。
**Output files:** tests/conftest.py (expanded), tests/test_database.py, tests/test_auth.py, tests/test_llm.py
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
@$HOME/.claude/get-shit-done/references/tdd.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/phase2_core_platform/02-RESEARCH.md

<infiles>web/database.py</infiles>
<infiles>web/models.py</infiles>
<infiles>web/auth.py</infiles>
<infiles>web/routers/auth.py</infiles>
<infiles>services/llm.py</infiles>
<infiles>scripts/init_db.py</infiles>
<infiles>tests/conftest.py</infiles>

<interfaces>
From web/database.py:
- `get_async_db()` — async generator, yields aiosqlite connection

From web/models.py:
- `VALID_TRANSITIONS: dict[str, list[str]]`
- `VideoStatus` enum
- All Create/Response BaseModels

From web/auth.py:
- `check_auth()` — Streamlit auth function (uses st.session_state)
- `verify_token(token: str = Depends(oauth2_scheme))` — FastAPI JWT dependency
- `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")`
- `login_for_access_token(form_data)` — creates JWT token
- `ALGORITHM = "HS256"`, `ACCESS_TOKEN_EXPIRE_HOURS = 24`

From services/llm.py:
- `LLMAbstract(function_id: str)` class
- `text_llm` / `multimodal_llm` global instances
- `chat(messages, **kwargs) -> str`
- `chat_json(messages, **kwargs) -> dict`

From tests/conftest.py:
- Existing `project_root` fixture
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
<name>Task 1: Update conftest.py + Create test_database.py</name>
<files>
tests/conftest.py
tests/test_database.py
</files>
<action>
**conftest.py 更新:**

在现有 fixtures 基础上添加：

1. `test_db_path(tmp_path)` fixture — 返回 `tmp_path / "test.db"` 路径
2. `init_test_db(test_db_path)` fixture — 调用 `scripts/init_db.init_database()` 写入临时路径（需要将 scripts/init_db.py 重构为可调用函数，或将 init_db.py 提取为 `def init_database(db_path: str)` 函数）

**CRITICAL:** settings.py 的 `settings = Settings()` 在导入时立即运行。任何访问 `settings.admin_password` 的测试都必须在导入设置**之前**通过 `monkeypatch.setenv("ADMIN_PASSWORD", "test_password")` 设置环境变量。建议在 conftest.py 中使用 `monkeypatch` 或 `pytest` 的 `autouse` fixture 处理。

**test_database.py 测试:**

1. `test_init_db_creates_tables(init_test_db)` — 验证 init_db 后所有 8 个表都存在
2. `test_init_db_wal_mode(init_test_db)` — 验证数据库文件启用了 WAL mode
3. `test_video_table_schema(init_test_db)` — 验证 videos 表有正确的列（id, title, status, topic_id 等）
4. `test_video_status_default(init_test_db)` — 验证新视频默认状态为 "idea"
5. `test_video_status_transitions(init_test_db)` — 使用 VALID_TRANSITIONS 字典单元测试状态转换
6. `test_video_invalid_transitions(init_test_db)` — 验证无效转换被拒绝（例如从 "idea" 直接到 "composing"）
7. `test_topic_insert(init_test_db)` — 验证 topics 表插入和读取
8. `test_script_insert(init_test_db)` — 验证 scripts 表插入和读取
9. `test_model_call_log_insert(init_test_db)` — 验证 model_call_logs 表插入

**behavior:**

Test: init_db creates all 8 tables
- Given: a fresh temporary database path
- When: init_database() is called
- Then: sqlite_master contains videos, topics, scripts, storyboards, model_call_logs, publish_queue, analytics_data, dialect_fixes

Test: WAL mode is enabled after init
- Given: a database initialized by init_db
- When: PRAGMA journal_mode is queried
- Then: result includes "wal"

Test: valid video state transitions
- Given: VALID_TRANSITIONS dict (imported from web.models)
- When: checking each from_state -> to_state pair defined in VALID_TRANSITIONS
- Then: every defined pair is valid

Test: invalid video state transitions
- Given: VALID_TRANSITIONS dict
- When: checking a transition that is NOT in VALID_TRANSITIONS[from_state]
- Then: the transition is rejected

Test: video status defaults to "idea"
- Given: a newly inserted video
- When: reading its status column
- Then: status equals "idea"

Test: model_call_log insert works
- Given: a model call log record
- When: inserting into model_call_logs table
- Then: the record can be read back with same values
</action>
<verify>
<automated>ADMIN_PASSWORD=test_password python -m pytest tests/test_database.py -x -q 2>&1</automated>
</verify>
<done>
test_database.py 中 9 个测试全部通过。conftest.py 提供可重用 fixtures 用于临时测试数据库。
</done>
</task>

<task type="auto" tdd="true">
<name>Task 2: Create test_auth.py</name>
<files>
tests/test_auth.py
</files>
<action>
创建 FastAPI JWT 认证测试。

**CRITICAL:** 必须在所有测试前通过 `monkeypatch.setenv("ADMIN_PASSWORD", "test_password")` 设置环境变量。由于 `settings = Settings()` 在导入时执行，必须在导入任何项目模块之前设置环境变量。在测试函数或 `conftest.py` 中使用 `monkeypatch.setenv`（注意 `monkeypatch.setenv` 在作用域内生效）。

对于 FastAPI 测试，使用 `from fastapi.testclient import TestClient`。TestClient 创建时不需要传入 lifespan 参数 —— 标准的 `TestClient(app)` 可以使用。

测试：

1. `test_jwt_token_creation(monkeypatch)` — monkeypatch 设置 ADMIN_PASSWORD，然后导入 jwt，创建 token 并解码验证
2. `test_jwt_token_has_expiry(monkeypatch)` — 验证 token 包含 `exp` 字段且在 24 小时后过期
3. `test_jwt_invalid_token_rejected(monkeypatch)` — 使用错误密码解码 token 时抛出 jwt.InvalidTokenError
4. `test_fastapi_token_endpoint(monkeypatch)` — 使用 TestClient POST /api/auth/token 并验证返回 access_token
5. `test_fastapi_token_wrong_password(monkeypatch)` — 使用错误密码时返回 401
6. `test_fastapi_protected_route_valid_token(monkeypatch)` — 使用有效 token 访问 /api/topics 返回 200
7. `test_fastapi_protected_route_no_token(monkeypatch)` — 不带 token 访问 /api/topics 返回 403（FastAPI 的 OAuth2PasswordBearer 返回 403 而非 401）

**behavior:**

Test: JWT token creation
- Given: admin_password = "test_password"
- When: token is created via jwt.encode with HS256
- Then: token can be decoded with settings.admin_password and contains "sub" claim

Test: JWT token has expiry
- Given: a token created with exp claim
- When: decoding the token
- Then: exp field is present and is a future timestamp

Test: invalid token rejected
- Given: a token signed with wrong password
- When: trying to decode with the correct password
- Then: jwt.InvalidTokenError is raised

Test: FastAPI /api/auth/token endpoint
- Given: TestClient(app) with correct form data (username="admin", password="test_password")
- When: POST /api/auth/token
- Then: response 200, response json has "access_token" and "token_type": "bearer"

Test: FastAPI /api/auth/token wrong password
- Given: TestClient(app) with wrong password
- When: POST /api/auth/token
- Then: response 401

Test: FastAPI protected route valid token
- Given: TestClient(app) with Authorization: Bearer {valid_token} header
- When: GET /api/topics
- Then: response 200

Test: FastAPI protected route no token
- Given: TestClient(app) without Authorization header
- When: GET /api/topics
- Then: response 403
</action>
<verify>
<automated>ADMIN_PASSWORD=test_password python -m pytest tests/test_auth.py -x -q 2>&1