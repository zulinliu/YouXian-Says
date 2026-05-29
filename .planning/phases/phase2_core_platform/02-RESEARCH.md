# Phase 2: Core Platform - Research

**Researched:** 2026-05-28
**Domain:** FastAPI async backend, SQLite WAL mode database, JWT authentication, LLM unified service, dual auth (Streamlit + FastAPI), database initialization
**Confidence:** HIGH

## Summary

Phase 2 builds the persistent foundation of the YouXian Says platform: a FastAPI async backend backed by SQLite (WAL mode), JWT-authenticated API routes, an LLM unified service with retry/JSON mode, Streamlit login authentication sharing the same credential as FastAPI JWT, and a database initialization script.

The architecture follows a dual-auth pattern: Streamlit pages use session-state-based password authentication, while FastAPI API routes use OAuth2PasswordBearer + PyJWT token verification, both sharing `settings.admin_password` as the shared secret. The database uses `aiosqlite` for async SQLite access from FastAPI endpoints, with a `lifespan` context manager for connection management.

The tech spec (section VI) provides exact code for database connection, Streamlit auth, FastAPI JWT auth, and LLMAbstract service. This research focuses on verifying recommendations, identifying library versions, and documenting pitfalls specific to async SQLite with FastAPI.

**Primary recommendation:** Use `aiosqlite` 0.22.1 for async SQLite with FastAPI `lifespan` context manager; use `PyJWT` 2.13.0 with `OAuth2PasswordBearer` for FastAPI JWT auth; use `openai.AsyncOpenAI` 1.30+ with `tenacity` retry for LLM service; the `admin_password` from `.env` serves as both Streamlit login password and JWT signing secret.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DB-01 | videos table with full state machine | Tech spec section VII defines state machine; sqlite3 3.45.1 supports all needed SQL features [VERIFIED: system install] |
| DB-02 | topics, scripts, storyboards tables | Standard SQLite tables; foreign keys reference videos table [VERIFIED: sqlite3 foreign_keys ON] |
| DB-03 | model_call_logs table | Schema defined in tech spec section 4.6.4; tracks all model calls with channel, tokens, latency, cost, quality [CITED: tech spec] |
| DB-04 | publish_queue table | Queue table with status, platform, scheduled time; SQLite supports all needed operations [VERIFIED: sqlite3 features] |
| DB-05 | analytics_data + dialect_fixes tables | Data collection and dialect optimization storage; simple schema [ASSUMED] |
| WEB-01 | SQLite WAL database connection | aiosqlite 0.22.1 supports WAL pragma via `await conn.execute("PRAGMA journal_mode=WAL")` [VERIFIED: venv install] |
| WEB-02 | Streamlit login + FastAPI JWT auth | Tech spec provides full auth.py code; PyJWT 2.13.0 with HS256 [VERIFIED: venv install + Context7 docs] |
| WEB-04 | FastAPI app + API routes | FastAPI 0.136.3 with uvicorn 0.48.0 [VERIFIED: venv install] |
| SVC-01 | LLM unified service with retry + JSON mode | openai 2.38.0 AsyncOpenAI; tenacity retry pattern in tech spec section 4.3 [VERIFIED: venv install + tech spec] |
| DATA-01 | init_db.py script | Creates all tables; runs PRAGMA WAL on database creation [ASSUMED] |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SQLite database connection | **FastAPI (async)** | -- | aiosqlite managed via lifespan context manager; single connection with WAL mode for concurrency |
| Database schema management | **scripts/init_db.py** | FastAPI startup | init_db.py creates tables at setup time; FastAPI startup verifies them |
| JWT token creation | **FastAPI backend** | -- | `/api/auth/token` endpoint issues JWT signed with `admin_password` as secret |
| JWT token verification | **FastAPI middleware** | -- | `OAuth2PasswordBearer` dependency on all protected routes |
| Streamlit login | **Streamlit session state** | FastAPI JWT | Streamlit checks `admin_password` directly; FastAPI uses same password as JWT secret |
| LLM unified service | **FastAPI / services** | -- | AsyncOpenAI client with retry; model routing via ModelRegistry.snapshot() |
| Database initialization | **Standalone script** | -- | `scripts/init_db.py` run once; idempotent with IF NOT EXISTS |
| API routes | **FastAPI** | -- | Router-based organization: topics, scripts, storyboards, auth, videos, analytics |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.136.3 | Async web framework | Auto-docs, dependency injection, async-native [VERIFIED: venv] |
| uvicorn | 0.48.0 | ASGI server | Standard FastAPI deployment; `uvicorn.run(app, host="127.0.0.1", port=8000)` [VERIFIED: venv] |
| aiosqlite | 0.22.1 | Async SQLite driver | Async WAL-mode SQLite; `async with aiosqlite.connect()` pattern [VERIFIED: venv] |
| PyJWT | 2.13.0 | JWT encode/decode | `jwt.encode(payload, key, algorithm="HS256")` for tokens [VERIFIED: venv + Context7] |
| openai | 2.38.0 | OpenAI-compatible API client | `AsyncOpenAI()` for LLM calls; supports `response_format={"type": "json_object"}` [VERIFIED: venv] |
| tenacity | latest | Retry library | `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))` [CITED: tech spec] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| streamlit | 1.57.0 | Web UI | For login page rendering and session state management [VERIFIED: venv] |
| httpx | 0.28.1 | Async HTTP client | For voice/image/video service API calls in future phases [VERIFIED: venv] |
| python-dotenv | latest | .env file loading | Bundled with pydantic-settings [VERIFIED: Phase 1] |
| pydantic-settings | 2.14.1 | Config management | Settings with .env file loading [VERIFIED: Phase 1] |
| cryptography | 41.0.7 | Fernet encryption | Required by PyJWT for RSA/EdDSA; installed on system [VERIFIED: Phase 1] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| aiosqlite | sqlite3 with ThreadPoolExecutor | aiosqlite provides proper async context managers; avoids blocking event loop [VERIFIED: Context7 docs] |
| PyJWT (python-jose) | PyJWT (jpadilla/pyjwt) | python-jose is unmaintained since 2021; jpadilla/pyjwt 2.13.0 is actively maintained and the standard [VERIFIED: PyPI] |
| OAuth2PasswordBearer | HTTPBearer | OAuth2PasswordBearer includes `tokenUrl` for OpenAPI docs auto-generation; HTTPBearer is lower-level [CITED: FastAPI docs] |
| admin_password as JWT secret | Separate JWT_SECRET env var | Tech spec uses admin_password; simpler for single-user setup. Separate secret is more secure for multi-user. [CITED: tech spec] |

**Installation:**
```bash
# Add to requirements.txt:
aiosqlite>=0.20.0
pyjwt>=2.8.0
```

**Version verification:**
```bash
# Verified 2026-05-28:
pip install aiosqlite  # -> 0.22.1
pip install pyjwt      # -> 2.13.0
```

## Architecture Patterns

### System Architecture Diagram

```
[Streamlit frontend]                  [FastAPI backend]
       |                                      |
       | (session state auth)                 | (JWT auth)
       | password === admin_password          | Bearer token
       |                                      |
       v                                      v
[web/pages/*.py] ---> HTTP/REST ---> [web/routers/*.py]
       |                                      |
       |                                      | Depends(auth)
       |                                      v
       |                            [services/llm.py]
       |                            LLMAbstract.chat_json()
       |                            | tenacity retry (3 attempts)
       |                            | openai.AsyncOpenAI
       |                            | ModelRegistry.snapshot()
       |                                      |
       |                                      v
       |                            [web/database.py]
       |                            get_async_db() async generator
       |                            | aiosqlite.connect()
       |                            | PRAGMA journal_mode=WAL
       |                            | PRAGMA busy_timeout=5000
       |                            | PRAGMA foreign_keys=ON
       |                                      |
       +-------- [scripts/init_db.py] --------> data/youxian.db
                 (CREATE TABLE IF NOT EXISTS)
                 (PRAGMA WAL)
```

### Recommended Project Structure
```
youxianduanshipin/
├── config/
│   ├── settings.py          # Pydantic Settings (admin_password shared secret)
│   └── model_registry.py    # ModelRegistry (from Phase 1)
├── services/
│   ├── llm.py               # LLMAbstract class (SVC-01)
│   └── ...                  # voice, digital_human, etc. (Phase 3)
├── web/
│   ├── app.py               # FastAPI + Streamlit combined entrypoint
│   ├── auth.py              # Streamlit check_auth() + FastAPI JWT verify_token()
│   ├── database.py          # get_async_db() async generator (WEB-01)
│   ├── models.py            # Pydantic models for API
│   ├── routers/
│   │   ├── auth.py          # POST /api/auth/token (WEB-02)
│   │   ├── topics.py        # /api/topics CRUD (DB-02)
│   │   ├── scripts.py       # /api/scripts CRUD (DB-02)
│   │   └── videos.py        # /api/videos status/state machine (DB-01)
│   └── pages/
│       └── settings.py      # Settings page (from Phase 1)
├── data/
│   └── youxian.db           # SQLite database file
├── scripts/
│   └── init_db.py           # Database initialization (DATA-01)
├── tests/
│   ├── test_database.py     # Database tests
│   ├── test_auth.py         # JWT auth tests
│   └── test_llm.py          # LLM service tests
└── pyproject.toml
```

### Pattern 1: Async SQLite Connection with FastAPI Lifespan
**What:** Use FastAPI's `lifespan` context manager to initialize and manage async SQLite connections. Use a dependency generator (`async generator`) to provide per-request connections.

**When to use:** For ALL database operations in FastAPI routes. Never use sync sqlite3 in async handlers.

**Example:**
```python
# web/database.py
import aiosqlite
from contextlib import asynccontextmanager

DB_PATH = "data/youxian.db"

async def get_db():
    """Async generator dependency for per-request database connection."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=5000")
        await db.execute("PRAGMA foreign_keys=ON")
        db.row_factory = aiosqlite.Row
        yield db

# In app.py:
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB is accessible
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("SELECT 1")
    yield
    # Shutdown: cleanup if needed

app = FastAPI(lifespan=lifespan)
```
[CITED: FastAPI docs - lifespan context manager; VERIFIED: aiosqlite 0.22.1 supports async with]

### Pattern 2: FastAPI JWT Auth with OAuth2PasswordBearer
**What:** Use `from fastapi.security import OAuth2PasswordBearer` to extract Bearer tokens, then decode with PyJWT using `admin_password` as the HS256 secret.

**When to use:** For ALL protected API routes. The `tokenUrl="/api/auth/token"` enables auto-generated OpenAPI docs with "Authorize" button.

**Example:**
```python
# web/auth.py
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from config.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
ALGORITHM = "HS256"

async def verify_token(token: str = Depends(oauth2_scheme)):
    """Dependency: verify JWT token, return username from 'sub' claim."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证令牌",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.admin_password, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except InvalidTokenError:
        raise credentials_exception

# Usage in router:
from fastapi import APIRouter, Depends
router = APIRouter()

@router.get("/api/protected")
async def protected_route(username: str = Depends(verify_token)):
    return {"user": username}
```
[CITED: FastAPI OAuth2 JWT tutorial; VERIFIED: PyJWT 2.13.0 Context7 docs]

### Pattern 3: Streamlit Login Sharing Same Credential
**What:** The Streamlit frontend checks `st.session_state.authenticated` against a password input. The password comparison uses `settings.admin_password`, which is the same value used as the JWT signing secret in FastAPI.

**When to use:** For the Streamlit login guard at the top of `web/app.py`.

**Example:**
```python
# web/app.py (Streamlit entrypoint)
import streamlit as st
from config.settings import settings

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("攸县有话说")
    password = st.text_input("管理员密码", type="password")
    if st.button("登录"):
        if password == settings.admin_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("密码错误")
    st.stop()
```
[CITED: tech spec section 6.1.2 - Streamlit login code]

### Pattern 4: LLM Unified Service with Retry and JSON Mode
**What:** The `LLMAbstract` class wraps `openai.AsyncOpenAI` with `tenacity` retry decorator and JSON mode support. Model routing via `ModelRegistry.snapshot()` for task isolation.

**When to use:** For ALL LLM calls in the system (topics, scripts, storyboards, analysis).

**Example:**
```python
# services/llm.py
import json
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config.model_registry import ModelRegistry

class LLMAbstract:
    """LLM统一调用层 — 自动路由到当前激活模型"""

    def __init__(self, function_id: str = "text_llm"):
        self.function_id = function_id

    def _get_client(self):
        model = ModelRegistry.snapshot(self.function_id)
        return AsyncOpenAI(
            api_key=model.resolved_api_key,
            base_url=model.api_base
        ), model.model_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    async def chat(self, messages: list, **kwargs) -> str:
        client, model_name = self._get_client()
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

    async def chat_json(self, messages: list, **kwargs) -> dict:
        """强制JSON输出格式。"""
        content = await self.chat(
            messages,
            response_format={"type": "json_object"},
            **kwargs
        )
        return json.loads(content)

# Global instances
text_llm = LLMAbstract("text_llm")
multimodal_llm = LLMAbstract("multimodal")
```
[CITED: tech spec section 4.3 - LLMAbstract code]

### Pattern 5: Database Initialization Script
**What:** A standalone Python script that creates all tables with IF NOT EXISTS. Runs `PRAGMA journal_mode=WAL` on first connect to ensure WAL mode is set for the database file.

**When to use:** Run once at setup time (`python scripts/init_db.py`).

**Example:**
```python
# scripts/init_db.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "youxian.db")

def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'idea',
            topic_id INTEGER,
            script_id INTEGER,
            storyboard_id INTEGER,
            dialect_dictionary TEXT,
            fact_risk_level TEXT DEFAULT 'confirmed_fact',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (topic_id) REFERENCES topics(id),
            FOREIGN KEY (script_id) REFERENCES scripts(id),
            FOREIGN KEY (storyboard_id) REFERENCES storyboards(id)
        );

        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            pillar TEXT,
            source TEXT DEFAULT 'user',
            status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );

        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            title TEXT,
            dialect_words TEXT,
            status TEXT DEFAULT 'draft',
            fact_check_notes TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );

        CREATE TABLE IF NOT EXISTS storyboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            shots TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );

        CREATE TABLE IF NOT EXISTS model_call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            model_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            channel TEXT NOT NULL,
            prompt_version TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            cost_estimate REAL DEFAULT 0,
            success INTEGER DEFAULT 0,
            error_message TEXT,
            quality_score REAL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS publish_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            scheduled_at TEXT,
            published_at TEXT,
            platform_post_id TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );

        CREATE TABLE IF NOT EXISTS analytics_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            date TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            collected_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        );

        CREATE TABLE IF NOT EXISTS dialect_fixes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            fixed_text TEXT NOT NULL,
            context TEXT,
            source TEXT DEFAULT 'user_review',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")
    print(f"WAL mode: {sqlite3.connect(DB_PATH).execute('PRAGMA journal_mode').fetchone()[0]}")

if __name__ == "__main__":
    init_database()
```
[ASSUMED: table schema design based on tech spec sections IV, VI, VII]

### Anti-Patterns to Avoid
- **Mixing sync and async database access:** Never use `sqlite3` (sync) inside async FastAPI routes. Always use `aiosqlite` for async endpoints. The event loop will be blocked by sync calls.
- **Not using `row_factory`:** By default, aiosqlite returns tuples, not dicts. Set `db.row_factory = aiosqlite.Row` to get column-name-accessible rows. [VERIFIED: aiosqlite docs]
- **Creating a new connection pool per request:** Use a single database path with `async with aiosqlite.connect()` (which creates a new connection) or a shared connection with proper lock management. WAL mode handles concurrent reads but SQLite still serializes writes.
- **Storing tokens in Streamlit session state without expiry:** JWT tokens have an `exp` claim. The Streamlit session just stores `authenticated = True` which persists until browser tab closes. Consider adding session timeout logic.
- **Using `admin_password` directly as JWT secret without salt:** The tech spec uses `settings.admin_password` as the JWT secret directly. For better security, consider using a dedicated `JWT_SECRET` environment variable. [ASSUMED: security best practice]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async SQLite | Raw `asyncio.subprocess` for sqlite3 | `aiosqlite` library | Proper async context managers, row factories, parameterized queries [VERIFIED: venv install] |
| JWT token handling | Custom base64 encoding/decoding | `PyJWT` library | Standardized RS256/HS256 support, expiry verification, aud/iss claims [VERIFIED: Context7] |
| HTTPBearer extraction | Manual Authorization header parsing | `fastapi.security.OAuth2PasswordBearer` | Built-in OpenAPI auto-docs, auto-error handling, dependency injection [CITED: FastAPI docs] |
| LLM API retry | Manual try/except loops | `tenacity` decorator | Exponential backoff, retry conditions, max attempts, clean syntax [CITED: tech spec] |
| LLM JSON mode | Manual JSON parsing with error handling | `response_format={"type": "json_object"}` | Guaranteed valid JSON output from supported models (GPT-4o, DeepSeek V4 Flash/Pro) [ASSUMED: openai API feature] |

**Key insight:** The tech spec already specifies all don't-hand-roll patterns above. The critical risk is the planner reverting to sync sqlite3 calls inside async FastAPI handlers, which would block the event loop.

## Common Pitfalls

### Pitfall 1: Blocking the Event Loop with Sync SQLite Calls
**What goes wrong:** Using `import sqlite3` (sync) inside async FastAPI route handlers blocks the event loop, degrading all concurrent requests.
**Why it happens:** Developers default to the familiar `sqlite3` module and forget that async routes run on a single-threaded event loop.
**How to avoid:** Always use `aiosqlite` in async routes. The tech spec's `database.py` uses sync `sqlite3` for simplicity, but for FastAPI async routes, use `aiosqlite`. [VERIFIED: aiosqlite docs]
**Warning signs:** Slow response times under concurrent requests; uvicorn warning about slow application.

### Pitfall 2: SQLite WAL and concurrent write contention
**What goes wrong:** SQLite serializes writes even in WAL mode. Concurrent write attempts from multiple async tasks will cause `database is locked` errors.
**Why it happens:** WAL mode allows concurrent reads + one writer. Multiple simultaneous writes queue up; the one that waits gets a timeout error.
**How to avoid:** Set `PRAGMA busy_timeout=5000` (5 seconds) to have SQLite retry automatically. This is already in the tech spec. For heavy write loads, consider a write queue or background task. [VERIFIED: sqlite3 PRAGMA docs]
**Warning signs:** `sqlite3.OperationalError: database is locked` in logs.

### Pitfall 3: aiosqlite `row_factory` not set
**What goes wrong:** `await cursor.fetchone()` returns a tuple `(1, 'title', 'idea', ...)` instead of a dict `{"id": 1, "title": "...", "status": "idea", ...}`.
**Why it happens:** aiosqlite defaults to tuple rows. The `Row` factory must be explicitly set.
**How to avoid:**
```python
async with aiosqlite.connect(DB_PATH) as db:
    db.row_factory = aiosqlite.Row  # Must set before queries
```
[VERIFIED: aiosqlite 0.22.1 docs]

### Pitfall 4: JWT token not including expiry (`exp`) claim
**What goes wrong:** Tokens without `exp` never expire. Compromised tokens are valid indefinitely.
**Why it happens:** The `jwt.encode()` function accepts any payload. The `exp` claim must be explicitly added.
**How to avoid:**
```python
from datetime import datetime, timedelta, timezone

payload = {"sub": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=24)}
token = jwt.encode(payload, settings.admin_password, algorithm="HS256")
```
[CITED: PyJWT docs - exp claim]

### Pitfall 5: Missing `WWW-Authenticate` header in 401 responses
**What goes wrong:** Browser/clients don't receive proper 401 challenge header, breaking the auth flow.
**Why it happens:** FastAPI's default 401 response may not include the `WWW-Authenticate: Bearer` header.
**How to avoid:** Explicitly add the header in the HTTPException:
```python
raise HTTPException(
    status_code=401,
    detail="无效的认证令牌",
    headers={"WWW-Authenticate": "Bearer"},
)
```
[CITED: FastAPI OAuth2 JWT tutorial]

### Pitfall 6: Streamlit rerun clears pending auth state
**What goes wrong:** On page rerun (e.g., after first button click), the password input clears before the auth check completes.
**Why it happens:** Streamlit reruns all code from top to bottom on every interaction.
**How to avoid:** The tech spec's pattern is correct: store `st.session_state.authenticated` and call `st.stop()` after showing login form. The `st.rerun()` inside the auth check ensures the page reloads with authenticated state. [VERIFIED: tech spec section 6.1.2]

## Code Examples

### Async SQLite Connection with Row Factory
```python
import aiosqlite
from fastapi import Depends

DB_PATH = "data/youxian.db"

async def get_async_db():
    """FastAPI dependency: provides async SQLite connection per request."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA busy_timeout=5000")
        await db.execute("PRAGMA foreign_keys=ON")
        db.row_factory = aiosqlite.Row
        yield db

# In router:
@router.get("/api/videos")
async def list_videos(db=Depends(get_async_db)):
    cursor = await db.execute("SELECT id, title, status FROM videos ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
```
[VERIFIED: aiosqlite Context7 docs]

### JWT Token Endpoint
```python
# web/routers/auth.py
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from config.settings import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return JWT token. Accepts any username with correct password."""
    if form_data.password != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = jwt.encode(
        {
            "sub": form_data.username or "admin",
            "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        },
        settings.admin_password,
        algorithm=ALGORITHM,
    )
    return {"access_token": access_token, "token_type": "bearer"}
```
[CITED: FastAPI OAuth2 JWT tutorial pattern]

### LLM Service: chat_json with Structured Output
```python
# Example usage of LLMAbstract.chat_json() for topic generation
from services.llm import text_llm

async def generate_topic_variations(idea: str) -> list[dict]:
    """Generate topic variations from a user idea."""
    result = await text_llm.chat_json([
        {
            "role": "system",
            "content": "你是一个攸县方言短视频选题策划。根据用户想法，生成5个不同角度的选题。"
        },
        {
            "role": "user",
            "content": f"我的想法是：{idea}"
        }
    ])
    return result.get("topics", [])
```
[CITED: tech spec section 4.3 - LLMAbstract with chat_json]

### Video State Machine Status Transitions
```python
# Status flow constants
VIDEO_STATUS_FLOW = [
    "idea",               # Initial state
    "topic_selected",     # Topic chosen
    "script_ready",       # Script generated
    "storyboard_ready",   # Storyboard designed
    "voice_ready",        # Voiceover generated
    "avatar_ready",       # Digital human video ready
    "broll_ready",        # B-roll clips ready
    "composing",          # FFmpeg composing
    "composed",           # Composition complete
    "pending_review",     # Awaiting human review
    "approved",           # Approved by human
    "publishing",         # Being published
    "published",          # Published successfully
    "rejected",           # Rejected (rollback)
]

# Allowed transitions
VALID_TRANSITIONS = {
    "idea": ["topic_selected"],
    "topic_selected": ["script_ready", "idea"],
    "script_ready": ["storyboard_ready", "topic_selected"],
    "storyboard_ready": ["voice_ready", "script_ready"],
    "voice_ready": ["avatar_ready", "script_ready"],
    "avatar_ready": ["broll_ready", "script_ready"],
    "broll_ready": ["composing", "script_ready"],
    "composing": ["composed"],
    "composed": ["pending_review"],
    "pending_review": ["approved", "rejected"],
    "approved": ["publishing"],
    "publishing": ["published"],
    "published": [],
    "rejected": ["script_ready", "topic_selected"],
}
```
[CITED: tech spec section VII - state machine; section X.3 - rollback levels]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FastAPI `startup`/`shutdown` event handlers | `lifespan` async context manager | FastAPI 0.94+ | Deprecated; use `@asynccontextmanager` instead [CITED: FastAPI docs] |
| python-jose (JWT) | PyJWT 2.x | python-jose unmaintained 2021 | python-jose has known security issues; PyJWT 2.13.0 is the maintained alternative [VERIFIED: PyPI] |
| Sync sqlite3 in FastAPI | aiosqlite for async routes | Continues improving | Sync calls block event loop; aiosqlite 0.22.1 provides proper async API [VERIFIED: venv] |
| Pydantic v1 `class Config:` | Pydantic v2 `model_config = SettingsConfigDict()` | Pydantic 2.0 (2023) | Incompatible; v1 config has no effect in v2 [VERIFIED: Phase 1 research] |

**Deprecated/outdated:**
- `python-jose` (PyJWT from `pip install python-jose`): unmaintained since 2021. Use `pip install pyjwt` (imported as `import jwt`) instead. [VERIFIED: PyPI]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | aiosqlite's `row_factory = aiosqlite.Row` returns dict-like rows that can be converted via `dict(row)` | Pattern 1 | May need to manually map column names; fallback to named tuple |
| A2 | The video state machine table schema with `status TEXT` column is sufficient for tracking | Code Examples, DB-01 | May need status_history table for audit trail; can add in later phase |
| A3 | `admin_password` as JWT HS256 secret is acceptable for single-user MVP | Pattern 2 | If multi-user needed later, add dedicated JWT_SECRET env var |
| A4 | `response_format={"type": "json_object"}` works with DeepSeek V4 Flash/Pro via OpenAI-compatible API | Pattern 4 | May not be supported by all providers; fallback to manual JSON parsing |
| A5 | Database schema design in init_db.py covers all fields needed by future phases | Pattern 5 | Migration may be needed in Phase 3+; use ALTER TABLE or recreate |
| A6 | `model_call_logs` table schema matches what the LLM service needs for logging | DB-03 | LLM service may need additional fields; schema is extensible |

## Open Questions

1. **Should FastAPI use a single shared async SQLite connection or per-request connections?**
   - What we know: aiosqlite's `async with aiosqlite.connect()` creates a new connection per request. WAL mode handles this well for reads.
   - What's unclear: Whether a single shared connection with explicit locking is more efficient for write-heavy workloads.
   - Recommendation: Use per-request connections with `busy_timeout=5000` for simplicity. If write contention issues appear, add a write queue or switch to a connection pool pattern.

2. **How should the Streamlit frontend call FastAPI endpoints?**
   - What we know: The tech spec shows Streamlit calling REST API for data operations.
   - What's unclear: Whether Streamlit should use `requests`/`httpx` to call FastAPI on localhost, or use shared Python imports directly.
   - Recommendation: Use shared Python imports via `import` for Streamlit-to-database calls (same process), and HTTP for external integrations. This avoids the overhead of localhost HTTP calls.

3. **Should status history be tracked in a separate table?**
   - What we know: The `videos` table has a `status` column showing current state.
   - What's unclear: Whether a `video_status_history` table is needed for audit trail / debugging.
   - Recommendation: Add `video_status_history` table in this phase to track transitions with timestamps. It is cheap storage and invaluable for debugging production issues.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Runtime | Yes | 3.12.3 | -- |
| SQLite 3.45+ | Database | Yes | 3.45.1 | -- |
| WAL mode | WEB-01 | Yes | Verified | -- |
| aiosqlite | Async DB | Installed | 0.22.1 | sync sqlite3 (blocks event loop) |
| PyJWT | JWT auth | Installed | 2.13.0 | -- |
| fastapi | API framework | Installed | 0.136.3 | -- |
| uvicorn | ASGI server | Installed | 0.48.0 | -- |
| openai | LLM client | Installed | 2.38.0 | -- |
| tenacity | Retry | Installed | latest | -- |
| httpx | Async HTTP | Installed | 0.28.1 | -- |
| streamlit | Web UI | Installed | 1.57.0 | -- |
| Playwright | Browser automation | Installed | 1.60.0 | -- |
| FFmpeg | Video processing | Installed | 6.1.1 | -- |

**Missing dependencies with no fallback:** None -- all required packages are installed and verified.

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest -x -q` (stop on first failure, quiet) |
| Full suite command | `pytest -v --tb=short` (verbose, short traceback) |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | init_db.py creates all tables | unit | `pytest tests/test_database.py::test_init_db_creates_tables -x` | Wave 0 |
| DATA-01 | init_db.py sets WAL mode | unit | `pytest tests/test_database.py::test_init_db_wal_mode -x` | Wave 0 |
| WEB-02 | Streamlit login accepts correct password | unit | `pytest tests/test_auth.py::test_streamlit_login -x` | Wave 0 |
| WEB-02 | FastAPI /api/auth/token returns JWT | integration | `pytest tests/test_auth.py::test_fastapi_jwt_token -x` | Wave 0 |
| WEB-02 | FastAPI verify_token rejects invalid JWT | integration | `pytest tests/test_auth.py::test_invalid_token_rejected -x` | Wave 0 |
| WEB-02 | FastAPI verify_token accepts valid JWT | integration | `pytest tests/test_auth.py::test_valid_token_accepted -x` | Wave 0 |
| WEB-04 | FastAPI app starts and serves routes | smoke | `pytest tests/test_database.py::test_app_startup -x` | Wave 0 |
| SVC-01 | LLMAbstract.chat returns string | unit | `pytest tests/test_llm.py::test_llm_chat_returns_string -x` | Wave 0 |
| SVC-01 | LLMAbstract.chat_json returns dict | unit | `pytest tests/test_llm.py::test_llm_chat_json_returns_dict -x` | Wave 0 |
| SVC-01 | LLM model routing via snapshot | unit | `pytest tests/test_llm.py::test_model_snapshot_routing -x` | Wave 0 |
| SVC-01 | Retry decorator on chat method | unit | `pytest tests/test_llm.py::test_retry_decorator_present -x` | Wave 0 |
| DB-01 | Video state machine valid transitions | unit | `pytest tests/test_database.py::test_video_status_transitions -x` | Wave 0 |
| DB-03 | model_call_logs insert works | unit | `pytest tests/test_database.py::test_model_call_log_insert -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest -x -q tests/test_database.py tests/test_auth.py`
- **Per wave merge:** `pytest -v --tb=short tests/`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_database.py` -- DATA-01, DB-01, DB-03 covers init_db, schema, state machine
- [ ] `tests/test_auth.py` -- WEB-02 covers Streamlit + FastAPI auth
- [ ] `tests/test_llm.py` -- SVC-01 covers LLM service pattern (mock OpenAI client)
- [ ] `tests/conftest.py` -- shared fixtures (temp db path, test settings, mock openai client)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Streamlit session state password + FastAPI JWT bearer token (HS256) |
| V3 Session Management | yes | JWT with `exp` claim (24h); Streamlit session state per browser tab |
| V4 Access Control | partial | Single-user system; no role-based access in MVP |
| V5 Input Validation | yes | Pydantic models for API request/response validation; aiosqlite parameterized queries prevent SQL injection |
| V6 Cryptography | partial | PyJWT HS256 for token signing; admin_password as secret key (shared credential) |

### Known Threat Patterns for Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via API input | Tampering | aiosqlite parameterized queries: `await db.execute("SELECT * FROM videos WHERE id=?", (vid,))` -- NEVER string formatting |
| JWT secret guessing | Information Disclosure | Require `admin_password` to be non-default, >= 16 chars; startup validation in settings.py |
| Token replay | Spoofing | Short `exp` window (24h); HTTPS recommended for production |
| Unauthorized DB access | Elevation of Privilege | `streamlit run web/app.py --server.address 127.0.0.1` binds to localhost only |
| Model API key leakage via error messages | Information Disclosure | Never include API keys in error responses; log errors server-side only |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: venv package install] -- aiosqlite 0.22.1, PyJWT 2.13.0, openai 2.38.0, fastapi 0.136.3, uvicorn 0.48.0, streamlit 1.57.0, httpx 0.28.1
- [VERIFIED: system install] -- Python 3.12.3, SQLite 3.45.1 (WAL mode confirmed), FFmpeg 6.1.1
- [CITED: tech spec document] -- 2026-05-28-youxian-tech-spec.md sections IV, VI: database connection, auth code, LLM service code, state machine, table schemas
- [VERIFIED: Context7 /fastapi/fastapi] -- FastAPI lifespan, dependency injection, SQLModel database setup
- [VERIFIED: Context7 /jpadilla/pyjwt] -- PyJWT encode/decode HS256, exp claim
- [VERIFIED: Context7 /websites/fastapi_tiangolo] -- OAuth2PasswordBearer, JWT auth tutorial, lifespan events

### Secondary (MEDIUM confidence)
- [VERIFIED: aiosqlite 0.22.1 installed] -- async with, row_factory, PRAGMA support confirmed

### Tertiary (LOW confidence)
- [ASSUMED] -- DeepSeek V4 Flash/Pro supports `response_format={"type": "json_object"}` via OpenAI-compatible API
- [ASSUMED] -- Video state machine table schema matches future phase requirements
- [ASSUMED] -- Single-user auth with shared admin_password/JWT secret is adequate for MVP

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all packages verified via install; versions documented
- Architecture: HIGH - tech spec provides complete patterns for all phase requirements
- Pitfalls: HIGH - verified via aiosqlite docs, FastAPI docs, PyJWT docs

**Research date:** 2026-05-28
**Valid until:** 2026-07-28 (stable stack; versions change slowly)
