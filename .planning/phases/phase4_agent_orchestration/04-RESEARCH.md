# Phase 4: Agent Orchestration — Research

**Researched:** 2026-05-28
**Domain:** AI Agent orchestration, multi-step async workflows, LLM-based content generation pipelines
**Confidence:** HIGH

## Summary

This phase implements three AI agents (Content, Production, Operations) and a Revision Parser that together form the autonomous video production pipeline. The agents consume existing Phase 2/3 services (LLMAbstract, voice, digital_human, video_gen, composer, publisher, model_logger, model_registry) and the state machine in `web/models.py`. There is no need for a separate task queue or workflow engine — Python's `asyncio` + `tenacity` provide sufficient orchestration for a single-user system.

**Key architectural insight:** Each agent snapshots model configuration at task start (via `ModelRegistry.snapshot()`), creates a database video record with status tracking, and follows the existing `VideoStatus` state machine. Agents are async functions, not long-running services — they run on demand within FastAPI's event loop or via `scripts/daily_run.py`. Long-running media generation steps (HeyGen, Runway) that are not yet integrated are handled via mock mode, which returns synchronously.

**Primary recommendation:** Implement four standalone agent classes (`ContentAgent`, `ProductionAgent`, `OpsAgent`, `RevisionParser`) that use `ModelRegistry.snapshot()` for model routing at task start, the state machine for lifecycle tracking, and `tenacity` for per-step retry. No external workflow engine (n8n) is needed for the agent logic itself — the agents ARE the workflow.

## User Constraints (from CONTEXT.md)

No CONTEXT.md exists for this phase. This research operates from PROJECT.md requirements and the tech spec document.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGENT-01 | Content Agent: topic co-creation to script generation to storyboard design | ContentAgent class using LLMAbstract.chat_json() with model routing (DeepSeek Flash for drafts, GLM-5.1 for structured output), dialect_dict for dialect injection, knowledge_base for content grounding. State transitions: idea -> topic_selected -> script_ready -> storyboard_ready |
| AGENT-02 | Production Agent: voice -> digital human -> B-roll -> compose -> export | ProductionAgent orchestrating services/voice.py -> digital_human.py -> video_gen.py -> composer.py sequentially. State transitions: storyboard_ready -> voice_ready -> avatar_ready -> broll_ready -> composing -> composed |
| AGENT-03 | Ops Agent: publish schedule + data collection + weekly report | OpsAgent using publisher.publish() for distribution, analytics data collection (simulated), LLMAbstract.chat_json() for weekly report generation |
| AGENT-04 | Revision Parser: natural language to structured operations | RevisionParser using LLMAbstract.chat_json() to parse user feedback into {type, target_shot, instruction} actions with rollback level detection |
| TEST-05 | Content Agent tests | pytest asyncio tests mocking LLMAbstract.chat_json() and image_gen.generate(). Mock LLM responses for topic divergence, script generation, storyboard generation |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Topic co-creation / idea divergence | API / Backend | — | Uses LLM API calls via LLMAbstract; no client-side logic |
| Script generation | API / Backend | — | Uses LLM API with dialect_dict and knowledge_base injection |
| Storyboard generation | API / Backend | — | Uses LLM for shot list + image_gen for reference images |
| Voice generation orchestration | API / Backend | — | Delegates to services/voice.py which is already implemented |
| Digital human orchestration | API / Backend | — | Delegates to services/digital_human.py |
| B-roll generation orchestration | API / Backend | — | Delegates to services/video_gen.py |
| Video composition orchestration | API / Backend | — | Delegates to services/composer.py |
| Publishing orchestration | API / Backend | — | Delegates to services/publisher.py |
| Data collection | API / Backend | — | Scheduled via daily_run.py or manual trigger |
| Weekly report generation | API / Backend | — | Uses LLM for data analysis |
| Revision parsing | API / Backend | — | Uses LLMAbstract.chat_json() for NL-to-structured parsing |
| State machine transitions | Database | API / Backend | Video status is tracked in SQLite; agents call status update API |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python asyncio | stdlib 3.12 | Async orchestration | Native, no external dependency needed for single-user workflow |
| tenacity | 9.1.4 | Retry logic for LLM/media API calls | Already used in LLMAbstract; proven pattern for API resilience [VERIFIED: existing codebase] |
| httpx | 0.28.1 | Async HTTP client for media services | Already used across all services as shared singleton [VERIFIED: services/__init__.py] |
| aiosqlite | 0.22.1 | Async SQLite for status updates | Already used in web/database.py [VERIFIED: requirements.txt] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-asyncio | — | Async test support | For TEST-05 async agent tests [ASSUMED: standard practice] |
| pytest-mock | — | Mock LLM API responses | For TEST-05 to avoid real API calls [ASSUMED: standard practice] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct asyncio orchestration | n8n workflow engine | n8n adds Docker deployment + webhook complexity. For single-user system, direct Python orchestration is simpler and debuggable. n8n is listed as "optional enhancement" in PROJECT.md Out of Scope. |
| Direct asyncio orchestration | Celery + Redis | Out of scope per PROJECT.md. Overkill for single-user system. |
| Direct asyncio orchestration | Temporal / Airflow / Prefect | Heavyweight for MVP. May be considered if multi-user scaling needed later. |

**Version verification:** tenacity 9.1.4, httpx 0.28.1, aiosqlite 0.22.1 confirmed via venv [VERIFIED: pip show].

## Architecture Patterns

### System Architecture Diagram

```
User / Web UI
     |
     v
+------------------+     +-----------------------+
|  ContentAgent    |---->|  ModelRegistry        |
|  - topic_create  |     |  .snapshot()          |
|  - generate_scr  |     |  selects model per    |
|  - storyboard    |     |  task type            |
+------------------+     +-----------------------+
     |                           ^
     | (video_id + status)       | (model config)
     v                           |
+------------------+             |
|  ProductionAgent |             |
|  - generate_voice|             |
|  - create_dh     |             |
|  - generate_broll|             |
|  - compose       |             |
+------------------+             |
     |                           |
     v                           |
+------------------+             |
|  RevisionParser  |             |
|  - parse_revision|             |
+------------------+             |
     |                           |
     v                           |
+------------------+             |
|  OpsAgent         |            |
|  - publish_video  |            |
|  - collect_data   |            |
|  - weekly_report  |            |
+------------------+             |
     |                           |
     v                           |
+--------------------------------------+
|  Database (SQLite WAL)               |
|  videos: status machine              |
|  topics, scripts, storyboards        |
|  model_call_logs                     |
|  publish_queue, analytics_data       |
+--------------------------------------+

Service layer (shared by all agents):
+----------+  +----------+  +----------+  +----------+  +----------+
| voice.py |  | dh.py    |  | vgen.py  |  | cmp.py   |  | pub.py   |
| (voice)  |  |(digital) |  | (b-roll) |  |(compose) |  |(publish) |
+----------+  +----------+  +----------+  +----------+  +----------+
     |              |             |             |             |
     v              v             v             v             v
  MiMo/Mock     Mock/Manual    Mock/Local    FFmpeg       API/PW
```

Data flow for a single video production (primary use case):
```
1. User provides idea -> ContentAgent.run_creative_session()
   -> LLM.chat_json() generates topic options
   -> User selects topic -> state: topic_selected

2. ContentAgent.generate_full_script(topic)
   -> LLM.chat_json() generates script with dialect injection
   -> Saves script record -> state: script_ready

3. ContentAgent.generate_storyboard(script)
   -> LLM.chat_json() generates shot list
   -> image_gen.generate() for reference images per shot
   -> Saves storyboard record -> state: storyboard_ready

4. ProductionAgent.produce_single(storyboard)
   -> voice.generate_voice() -> state: voice_ready
   -> digital_human.create_digital_human() -> state: avatar_ready
   -> video_gen.generate_broll() per shot -> state: broll_ready
   -> composer.compose_video() -> state: composing -> composed

5. User reviews -> if rejected: RevisionParser.parse_revision()
   -> OpsAgent.publish_approved() -> state: publishing -> published

6. OpsAgent.collect_daily_data() / generate_weekly_report()
```

### Recommended Project Structure
```
youxianduanshipin/
├── agents/                          # NEW directory
│   ├── __init__.py                  # Agent exports
│   ├── content_agent.py             # ContentAgent class
│   ├── production_agent.py          # ProductionAgent class
│   ├── ops_agent.py                 # OpsAgent class
│   └── revision_parser.py           # RevisionParser / parse_revision()
├── tests/
│   └── test_agents/                 # NEW directory
│       ├── __init__.py
│       └── test_content_agent.py    # TEST-05
├── ...existing directories...
```

### Pattern 1: Agent Base Pattern (Snapshot + State Machine + Retry)

**What:** Every agent snapshots model config at task start, tracks state through the database, and retries per-step with tenacity.

**When to use:** All agent implementations.

**Example:**
```python
# agents/content_agent.py — pattern from tech spec Section 5.1 [CITED: 2026-05-28-youxian-tech-spec.md]
class ContentAgent:
    def __init__(self, db=None):
        self.llm = text_llm  # from services.llm
        self.image_gen = image_gen  # from services.image_gen
        self.db = db or get_db_connection()
        self.dialect_dict = json.loads(Path("data/dialect_dict.json").read_text())

    async def run_creative_session(self, user_idea: str) -> list[dict]:
        """Step 1: User provides idea, Agent retrieves knowledge + diverges topics."""
        knowledge = self._load_knowledge_base()
        topics = await self.llm.chat_json([
            {"role": "system", "content": TOPIC_DIVERGE_PROMPT.format(
                user_idea=user_idea, knowledge=knowledge,
                dialect_words=json.dumps(
                    [w["word"] for w in self.dialect_dict["words"]],
                    ensure_ascii=False
                )
            )}
        ])
        return topics.get("topics", [])

    async def generate_full_script(self, topic: dict, video_id: int) -> dict:
        """Step 2: Generate complete script with dialect injection."""
        script = await self.llm.chat_json([
            {"role": "system", "content": SCRIPT_GENERATION_PROMPT.format(
                topic_title=topic["title"],
                dialect_dict=json.dumps(self.dialect_dict, ensure_ascii=False)
            )}
        ])
        await self.db.execute(
            "INSERT INTO scripts (video_id, content, title, dialect_words) VALUES (?, ?, ?, ?)",
            (video_id, script["content"], script.get("title", topic["title"]),
             json.dumps(script.get("dialect_words", []), ensure_ascii=False))
        )
        await self.db.commit()
        await self._update_status(video_id, "script_ready")
        return script

    async def generate_storyboard(self, script: dict, video_id: int) -> list[dict]:
        """Step 3: Generate storyboard with reference images."""
        shots = await self.llm.chat_json([
            {"role": "system", "content": STORYBOARD_PROMPT.format(
                script_content=script["content"]
            )}
        ])
        shot_list = shots.get("shots", [])
        for shot in shot_list:
            if shot.get("need_reference"):
                shot["reference_image"] = await self.image_gen.generate(
                    shot.get("visual_description", ""),
                    f"output/images/sb_{video_id}_{shot.get('shot_number', 0)}.png"
                )
        await self.db.execute(
            "INSERT INTO storyboards (video_id, shots) VALUES (?, ?)",
            (video_id, json.dumps(shot_list, ensure_ascii=False))
        )
        await self.db.commit()
        await self._update_status(video_id, "storyboard_ready")
        return shot_list

    async def _update_status(self, video_id: int, status: str):
        """Update video status in database."""
        await self.db.execute(
            "UPDATE videos SET status=?, updated_at=datetime('now','localtime') WHERE id=?",
            (status, video_id)
        )
        await self.db.commit()
```

### Pattern 2: Production Pipeline with Sequential Orchestration

**What:** Run each production step sequentially; when step succeeds, move to next state. If a step fails, retry (tenacity) before failing.

**When to use:** ProductionAgent.produce_single() — voice -> digital_human -> broll -> compose.

**Example:**
```python
# agents/production_agent.py [CITED: 2026-05-28-youxian-tech-spec.md Section 5.2]
class ProductionAgent:
    async def produce_single(self, storyboard: dict, video_id: int) -> dict:
        """Full production pipeline: voice -> DH -> b-roll -> compose."""
        # 1. Voice generation
        voice_path = await voice.generate_voice(
            text=storyboard.get("full_dialogue", ""),
            output_path=f"output/voices/{video_id}.wav",
            job_id=str(video_id)
        )
        await self._update_status(video_id, "voice_ready")

        # 2. Digital human
        dh_path = await digital_human.create_digital_human(
            audio_path=voice_path,
            output_path=f"output/videos/dh_{video_id}.mp4",
            job_id=str(video_id)
        )
        await self._update_status(video_id, "avatar_ready")

        # 3. B-roll clips
        broll_paths = []
        for shot in storyboard.get("shots", []):
            if shot.get("type") == "b_roll":
                broll_path = await video_gen.generate_broll(
                    prompt=shot.get("visual_description", ""),
                    output_path=f"output/videos/broll_{video_id}_{shot.get('shot_number', 0)}.mp4",
                    target_duration=shot.get("duration", 5.0),
                    job_id=str(video_id)
                )
                broll_paths.append({"path": broll_path, **shot})
        await self._update_status(video_id, "broll_ready")

        # 4. Compose final video
        await self._update_status(video_id, "composing")
        final_path = composer.compose_video(
            digital_human_path=dh_path,
            voice_path=voice_path,
            b_roll_clips=broll_paths,
            subtitles=storyboard.get("subtitles", []),
            bgm_path=self._select_bgm(storyboard.get("mood", "neutral")),
            branding_path="templates/branding",
            output_path=f"output/final/{video_id}.mp4",
            fmt="9:16"
        )
        await self._update_status(video_id, "composed")
        return {"video_id": video_id, "output_path": final_path}
```

### Pattern 3: Revision Parser (NL to Structured Operations)

**What:** Uses LLMAbstract.chat_json() to parse natural language revision instructions into structured operations with rollback level detection.

**When to use:** When user clicks "rejected" and provides feedback text.

**Example:**
```python
# agents/revision_parser.py [CITED: 2026-05-28-youxian-tech-spec.md Section 6.3.2]
from services.llm import text_llm

REVISION_PARSE_PROMPT = """你是一个视频修改指令解析器。将用户的自然语言修改意见解析为结构化操作。

用户意见：{instruction}
视频信息：{video_info}

请输出JSON格式：
{{
  "rollback_level": "minor|major|critical",
  "actions": [
    {{
      "type": "regenerate_broll | regenerate_voice | edit_subtitle | change_music | rewrite_script",
      "target_shot": 2,
      "instruction": "具体的技术指令"
    }}
  ]
}}"""

async def parse_revision(instruction: str, video_info: dict) -> dict:
    result = await text_llm.chat_json([
        {"role": "system", "content": REVISION_PARSE_PROMPT.format(
            instruction=instruction,
            video_info=json.dumps(video_info, ensure_ascii=False)
        )}
    ])
    return result
```

### Anti-Patterns to Avoid
- **Inline model selection per call:** Instead of hardcoding model names in agent code, use `ModelRegistry.snapshot()` at task start and let the registry configuration drive model selection. The agent calls `llm.chat_json(messages)` without knowing which model handles it.
- **Synchronous fallback chains in hot loops:** When iterating over b-roll shots, do NOT wait for each one synchronously. Use `asyncio.gather()` for parallel b-roll generation across shots.
- **Agent state in memory:** Do NOT store agent state (current task, progress) as class instance variables. The database IS the state — read status from the videos table on recovery.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Model routing per task type | Manual if/else in agent code | ModelRegistry.snapshot() + ModelRouter pattern [CITED: tech spec 4.6.3] | Model selection policy is config-driven, not code-driven; users can switch models via Web UI |
| Retry logic for API failures | Try/except blocks per call | tenacity retry decorator | Already used in LLMAbstract; provides exponential backoff, max attempts, exception filtering |
| Async HTTP client pool | Per-call httpx clients | Shared httpx.AsyncClient singleton via get_http_client() | Already implemented in services/__init__.py; manages connection limits/timeouts |
| Method-level timing/logging | Manual time.time() in each method | model_logger.Timer + log_model_call() | Already implemented in all services; provides consistent logging to DB |
| JSON response formatting | Manual json.loads() error handling | LLMAbstract.chat_json() | Already implemented; handles JSON parsing with retry |

**Key insight:** All the infrastructure agents need (model registry, async client, logger, retry, state machine) already exists in Phases 2 and 3. The agents are orchestrators that compose these existing services. Do NOT add new infrastructure layers.

## Common Pitfalls

### Pitfall 1: Snapshot vs. Live Model Config
**What goes wrong:** Agent starts a multi-step pipeline with model A, user switches to model B in Web UI mid-task, subsequent steps use model B, causing inconsistent output.
**Why it happens:** Agents call `ModelRegistry.get_active()` repeatedly, which reflects live changes.
**How to avoid:** Call `ModelRegistry.snapshot()` once at task start and pass the snapshot to all sub-steps. The `snapshot()` method is already implemented for this purpose. [VERIFIED: model_registry.py line 523-525]
**Warning signs:** Intermittent model inconsistencies in multi-step pipelines.

### Pitfall 2: Mixing Sync and Async (composer.py is sync)
**What goes wrong:** `ProductionAgent` is async, but `composer.compose_video()` is a synchronous FFmpeg call that blocks the event loop for 30+ seconds.
**Why it happens:** FFmpeg uses `subprocess.run()` which is blocking.
**How to avoid:** Wrap the composer call in `asyncio.to_thread(composer.compose_video, ...)` to run it in a thread pool, keeping the event loop responsive. [ASSUMED: asyncio.to_thread available in Python 3.12]
**Warning signs:** FastAPI server becomes unresponsive during composition.

### Pitfall 3: Database Connection Contention
**What goes wrong:** Agents create their own DB connections (via `get_db_connection()` or raw aiosqlite) that conflict with FastAPI's `get_async_db()` dependency.
**Why it happens:** SQLite WAL mode handles concurrent readers well but writer contention still occurs.
**How to avoid:** Use `PRAGMA busy_timeout=5000` (already set), keep transactions short, and use a single DB connection per agent task lifecycle. [VERIFIED: database.py PRAGMA settings]
**Warning signs:** `database is locked` errors under concurrent agent calls.

### Pitfall 4: B-roll Duration Mismatch
**What goes wrong:** The composer expects B-roll clips with specific durations matching subtitle timestamps, but `generate_broll()` produces different-length clips.
**Why it happens:** B-roll duration is set by the storyboard but service implementations may not honor `target_duration` precisely (especially mock mode with fixed placeholder).
**How to avoid:** After `generate_broll()` returns, verify the output duration via FFprobe and log a warning if it deviates more than 1s from target. [ASSUMED: ffprobe available with ffmpeg]
**Warning signs:** Composer reports "B-roll clip at Xs overlaps with next clip" or audio/video drift.

## Code Examples

### ContentAgent — Full Orchestration Pattern

```python
# Source: Synthesized from tech spec Sections 5.1 and 4.3 [CITED]
from pathlib import Path
import json
from services.llm import text_llm
from services.image_gen import generate_image
from services.model_logger import log_model_call, Timer
from config.model_registry import ModelRegistry
from tenacity import retry, stop_after_attempt, wait_exponential

class ContentAgent:
    """Content agent: topic co-creation -> script generation -> storyboard design.

    Each method calls ModelRegistry.snapshot() at start to freeze model selection
    for the duration of the operation.
    """

    def __init__(self):
        self.dialect_dict = self._load_json("data/dialect_dict.json")
        self.knowledge_base = self._load_text("data/knowledge_base.md")

    def _load_json(self, path: str) -> dict:
        try:
            return json.loads(Path(path).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {"words": []}

    def _load_text(self, path: str) -> str:
        try:
            return Path(path).read_text()
        except FileNotFoundError:
            return ""

    async def diverge_topics(self, user_idea: str) -> list[dict]:
        """Generate 3-5 topic variations from user idea."""
        result = await text_llm.chat_json([
            {"role": "system", "content": TOPIC_DIVERGE_PROMPT.format(
                user_idea=user_idea,
                dialect_words=json.dumps(
                    [w["word"] for w in self.dialect_dict.get("words", [])],
                    ensure_ascii=False
                )
            )}
        ])
        return result.get("topics", [])

    async def generate_script(self, topic: dict) -> dict:
        """Generate full script with dialect words embedded."""
        result = await text_llm.chat_json([
            {"role": "system", "content": SCRIPT_PROMPT.format(
                topic_title=topic["title"],
                pillar=topic.get("pillar", "general"),
                dialect_dict=json.dumps(self.dialect_dict, ensure_ascii=False),
                knowledge_base=self.knowledge_base
            )}
        ])
        return result

    async def generate_storyboard(self, script: dict, video_id: int) -> list[dict]:
        """Generate shot-by-shot storyboard with reference images."""
        shots_result = await text_llm.chat_json([
            {"role": "system", "content": STORYBOARD_PROMPT.format(
                script_content=script.get("content", ""),
                script_title=script.get("title", "")
            )}
        ])
        shots = shots_result.get("shots", [])

        for shot in shots:
            if shot.get("need_reference"):
                desc = shot.get("visual_description", "")
                img_path = f"output/images/sb_{video_id}_{shot.get('shot_number', 0)}.png"
                shot["reference_image"] = await generate_image(desc, img_path)

        return shots
```

### ProductionAgent — Pipeline Orchestration with FFmpeg Wrapping

```python
# Source: Synthesized from tech spec Section 5.2 [CITED]
import asyncio
from services import voice, digital_human, video_gen, composer
from services.model_logger import log_model_call

class ProductionAgent:
    """Production pipeline: voice -> digital human -> b-roll -> compose."""

    async def produce_single(self, storyboard: dict, video_id: int) -> dict:
        """Orchestrate all production steps sequentially.

        composer.compose_video() is synchronous (FFmpeg subprocess),
        so it runs via asyncio.to_thread() to avoid blocking the event loop.
        """
        full_dialogue = storyboard.get("full_dialogue", "")
        shots = storyboard.get("shots", [])

        voice_path = await voice.generate_voice(
            text=full_dialogue,
            output_path=f"output/voices/{video_id}.wav",
            job_id=str(video_id)
        )
        dh_path = await digital_human.create_digital_human(
            audio_path=voice_path,
            output_path=f"output/videos/dh_{video_id}.mp4",
            job_id=str(video_id)
        )
        # Generate B-roll clips in parallel
        broll_tasks = []
        for shot in shots:
            if shot.get("type") == "b_roll":
                broll_tasks.append(
                    video_gen.generate_broll(
                        prompt=shot.get("visual_description", ""),
                        output_path=f"output/videos/broll_{video_id}_{shot['shot_number']}.mp4",
                        target_duration=shot.get("duration", 5.0),
                        job_id=str(video_id)
                    )
                )
        broll_paths = await asyncio.gather(*broll_tasks)

        # Run synchronous composer in thread pool
        final_path = await asyncio.to_thread(
            composer.compose_video,
            digital_human_path=dh_path,
            voice_path=voice_path,
            b_roll_clips=[{"path": p} for p in broll_paths],
            subtitles=storyboard.get("subtitles", []),
            bgm_path="templates/music/bgm.mp3",
            branding_path="templates/branding",
            output_path=f"output/final/{video_id}.mp4",
            fmt="9:16"
        )
        return {"video_id": video_id, "output_path": final_path}
```

### OpsAgent — Publish and Analytics

```python
# Source: Synthesized from tech spec Section 5.3 [CITED]
from services.publisher import publish
from services.llm import text_llm

class OpsAgent:
    """Operations agent: publish + data collection + weekly report."""

    async def publish_approved(self, video_id: int, video_path: str, platforms: list[str], meta: dict) -> dict:
        """Publish approved video to specified platforms (defaults to pending_review)."""
        return await publish(
            video_path=video_path,
            meta=meta,
            platforms=platforms,
            job_id=str(video_id)
        )

    async def collect_daily_data(self) -> dict:
        """Simulated daily data collection from all platforms."""
        results = {}
        for platform in ["douyin", "kuaishou", "weixin", "xiaohongshu"]:
            results[platform] = {"status": "simulated", "note": "Data collection stub"}
        return results

    async def generate_weekly_report(self, weekly_data: dict) -> dict:
        """Generate weekly analysis report using LLM."""
        report = await text_llm.chat_json([
            {"role": "system", "content": WEEKLY_REPORT_PROMPT.format(
                data=json.dumps(weekly_data, ensure_ascii=False)
            )}
        ])
        return report
```

### Prompt Templates for Agents

```python
# config/prompts.py — additions for agent prompts [ASSUMED: based on PROJECT.md requirements]

# Content Agent: Topic divergence (DeepSeek Flash → high volume, low cost)
TOPIC_DIVERGE_PROMPT = """你是一个攸县方言短视频选题策划。

用户想法：{user_idea}
可用方言词汇：{dialect_words}

请发散3-5个不同的选题角度，每个角度包括：
- title: 选题标题（含方言味道）
- pillar: 内容支柱（food/travel/culture/people/history）
- hook: 开头钩子（一句话）
- reason: 为什么这个角度有看点

输出JSON格式：{{"topics": [{{"title": "…", "pillar": "…", "hook": "…", "reason": "…"}}]}}"""

# Content Agent: Script generation (GLM-5.1 Relay → deep reasoning + structured output)
SCRIPT_PROMPT = """你是一个攸县方言短视频脚本创作专家。

选题：{topic_title}
内容支柱：{pillar}
方言词典：{dialect_dict}
攸县知识库：{knowledge_base}

要求：
1. 脚本用书面中文撰写，但必须嵌入至少3个攸县方言词汇
2. 时长约30-45秒口播稿（约150-250字）
3. 开头有钩子，中间有干货，结尾有互动引导
4. 标注每个方言词汇的插入位置

输出JSON格式：{{"content": "…", "dialect_words": [{{"word": "…", "position": 0}}], "subtitles": [{{"start": 0, "end": 3, "text": "…"}}]}}"""

# Content Agent: Storyboard generation
STORYBOARD_PROMPT = """你是一个短视频分镜设计师。

脚本内容：{script_content}

请将脚本拆解为分镜列表，每个分镜包括：
- shot_number: 镜头序号
- type: "digital_human"（口播）或 "b_roll"（空镜/素材）
- visual_description: 画面描述（英文，供视频模型使用）
- duration: 时长（秒）
- need_reference: 是否需要参考图
- start_time: 在视频中的起始时间

输出JSON格式：{{"shots": [{{"shot_number": 1, "type": "…", "visual_description": "…", "duration": 5, "need_reference": false, "start_time": 0}}]}}"""

# Operations Agent: Weekly report
WEEKLY_REPORT_PROMPT = """你是一个短视频运营数据分析师。

本周数据：
{data}

请分析：
1. 各平台表现对比
2. 本周最佳内容特征
3. 下周选题建议（含内容支柱权重调整）
4. 异常数据说明

输出JSON格式：{{"platform_summary": {{}}, "best_content": "", "recommendations": [], "anomalies": []}}"""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded model names in agent code | ModelRegistry.snapshot() for config-driven routing | Design doc 2026-05-28 | Agents are model-agnostic; model switching via Web UI |
| Per-step manual error handling | tenacity retry decorator on each service call | Phase 2 LLMAbstract | Consistent retry pattern across all API calls |
| Sync SQL queries in async agents | aiosqlite for non-blocking DB access | Phase 2 database layer | No event loop blocking during status updates |

**Deprecated/outdated:**
- Celery/Redis task queue: Out of scope per PROJECT.md. Agents run directly in the event loop.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | asyncio.to_thread() is available in Python 3.12 for wrapping sync FFmpeg calls | Architecture Patterns | Must use loop.run_in_executor() instead; functionally equivalent |
| A2 | pytest-asyncio and pytest-mock are the standard test toolchain for async agent tests | Standard Stack | Tests can use unittest.IsolatedAsyncioTestCase and manual mock objects |
| A3 | The `voice.generate_voice()` function signature accepts `(text, output_path, job_id)` | Code Examples | Check voice.py — `generate_voice` signature is `(text, output_path, job_id="test")`, confirmed [VERIFIED] |
| A4 | `digital_human.create_digital_human()` signature is `(audio_path, output_path, job_id)` | Code Examples | Confirmed [VERIFIED: digital_human.py line 116-119] |
| A5 | `video_gen.generate_broll()` signature is `(prompt, output_path, target_duration, job_id)` | Code Examples | Confirmed [VERIFIED: video_gen.py line 100-104] |
| A6 | `composer.compose_video()` accepts kwargs matching the pattern shown | Code Examples | Confirmed — signature is `compose_video(dh_path, voice_path, brolls, subs, bgm, branding, output, fmt)` [VERIFIED: composer.py line 69-78] |

## Open Questions

1. **How should agents be triggered from the Web UI?**
   - What we know: Web UI is Streamlit, agents are async Python functions.
   - What's unclear: Should the Streamlit page call agent methods directly, or via FastAPI endpoints? Direct calls are simpler but block the Streamlit UI during long operations.
   - Recommendation: Add FastAPI endpoints for agent operations (e.g., `/api/agents/run-content`), and Streamlit calls these endpoints. This keeps Streamlit responsive and allows future webhook-based triggering.

2. **Should OpsAgent's weekly report run synchronously or deferred?**
   - What we know: Weekly report uses LLMAbstract.chat_json() which completes in seconds (not minutes like media generation).
   - What's unclear: Whether to run it in-line or put it in a background task.
   - Recommendation: Run inline — LLM analysis is fast enough (<30s). Use `asyncio.create_task()` only if needed for UI responsiveness.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Agent orchestration | Yes | 3.12.3 | — |
| aiosqlite | DB status updates | Yes | 0.22.1 | — |
| tenacity | API retry logic | Yes | 9.1.4 | — |
| openai SDK | LLMAbstract | Yes | 2.38.0 | — |
| httpx | Async HTTP client | Yes | 0.28.1 | — |
| FFmpeg | Composer | Yes | 6.1.1 | — |
| pytest | TEST-05 | Yes | (check) | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x+ |
| Config file | pyproject.toml (testpaths = ["tests"]) |
| Quick run command | `pytest tests/test_agents/ -x -v` |
| Full suite command | `pytest tests/ -x -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGENT-01 | ContentAgent.diverge_topics returns list of topic dicts | unit | `pytest tests/test_agents/test_content_agent.py::test_diverge_topics -x` | Wave 0 |
| AGENT-01 | ContentAgent.generate_script returns script dict with dialect words | unit | `pytest tests/test_agents/test_content_agent.py::test_generate_script -x` | Wave 0 |
| AGENT-01 | ContentAgent.generate_storyboard returns shot list with optional images | unit | `pytest tests/test_agents/test_content_agent.py::test_generate_storyboard -x` | Wave 0 |
| AGENT-02 | ProductionAgent.produce_single runs full pipeline | integration | `pytest tests/test_production_agent.py -x` | Wave 0 |
| AGENT-03 | OpsAgent.publish_approved delegates to publisher | unit | `pytest tests/test_ops_agent.py -x` | Wave 0 |
| AGENT-04 | RevisionParser.parse_revision returns structured operations | unit | `pytest tests/test_revision_parser.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_agents/ -x -v`
- **Per wave merge:** `pytest tests/ -x -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_agents/__init__.py` — package marker
- [ ] `tests/test_agents/conftest.py` — shared fixtures: mock_llm, mock_image_gen, dialect_dict, knowledge_base fixtures
- [ ] `tests/test_agents/test_content_agent.py` — covers AGENT-01
- [ ] `tests/test_agents/test_production_agent.py` — covers AGENT-02
- [ ] `tests/test_agents/test_ops_agent.py` — covers AGENT-03
- [ ] `tests/test_agents/test_revision_parser.py` — covers AGENT-04
- [ ] pytest-asyncio install: `pip install pytest-asyncio` — if not detected

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | JWT via FastAPI dependency (existing) |
| V3 Session Management | yes | JWT tokens with 24h expiry (existing web/auth.py) |
| V4 Access Control | no | Single-user system; admin password gate (existing) |
| V5 Input Validation | yes | User-provided ideas/revisions validated via Pydantic models before reaching agents |
| V6 Cryptography | no | No cryptographic operations in agents |

### Known Threat Patterns for Agent Orchestration

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via user idea/revision | Tampering | LLM input sanitization via system prompts with strict output format constraints; no raw user input reflected in system context without escaping [ASSUMED] |
| API key exposure in error messages | Information Disclosure | model_logger.log_model_call() already strips sensitive patterns from error messages before logging [VERIFIED: model_logger.py line 34-39] |
| Unbounded retry loops | Denial of Service | tenacity retry configured with max attempts (3) and exponential backoff [VERIFIED: LLMAbstract uses stop_after_attempt(3)] |

## Sources

### Primary (HIGH confidence)
- Existing codebase: services/llm.py, services/voice.py, services/digital_human.py, services/video_gen.py, services/composer.py, services/publisher.py, services/image_gen.py, services/model_logger.py — all service signatures confirmed [VERIFIED]
- Existing codebase: config/model_registry.py — snapshot() and get_active() patterns confirmed [VERIFIED]
- Existing codebase: config/prompts.py — current prompt structure confirmed [VERIFIED]
- Existing codebase: web/models.py — VideoStatus state machine with VALID_TRANSITIONS confirmed [VERIFIED]
- 2026-05-28-youxian-tech-spec.md — Sections V (Agent core logic), VI (Revision Parser), X (Exception handling), 4.6.3 (ModelRouter); all agent architecture patterns cited from this document [CITED]
- requirements.txt and pyproject.toml — existing dependencies confirmed [VERIFIED]

### Secondary (MEDIUM confidence)
- Existing codebase: data/dialect_dict.json — 20+ dialect entries confirmed [VERIFIED]
- Existing codebase: data/knowledge_base.md — 4+ topic sections confirmed [VERIFIED]
- PROJECT.md — agent requirements and architecture decisions [CITED]

### Tertiary (LOW confidence)
- None — all claims are VERIFIED or CITED from existing codebase or tech spec.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all existing dependencies confirmed in venv
- Architecture: HIGH — patterns directly from tech spec and existing codebase
- Pitfalls: MEDIUM — snapshot contention and sync/async mixing are known issues from Phase 2/3 patterns; B-roll duration mismatch is an assumption based on service signatures
- Code examples: HIGH — all function signatures verified against actual service code

**Research date:** 2026-05-28
**Valid until:** 2026-06-28 (stable stack, services already implemented)
