---
phase: phase4_agent_orchestration
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - agents/__init__.py
  - agents/content_agent.py
  - agents/production_agent.py
  - agents/ops_agent.py
  - agents/revision_parser.py
  - config/prompts.py
  - tests/test_agents/__init__.py
  - tests/test_agents/conftest.py
  - tests/test_agents/test_content_agent.py
  - tests/test_agents/test_revision_parser.py
autonomous: true
requirements: [AGENT-01, AGENT-02, AGENT-03, AGENT-04, TEST-05]

must_haves:
  truths:
    - "ContentAgent can diverge user idea into multiple topic options via LLM"
    - "ContentAgent can generate a full script with dialect words injected"
    - "ContentAgent can generate a storyboard shot list with reference images"
    - "ProductionAgent can orchestrate voice -> digital human -> b-roll -> compose sequentially"
    - "ProductionAgent wraps synchronous FFmpeg composer in asyncio.to_thread() for async safety"
    - "OpsAgent can publish approved video, collect daily data, and generate weekly report"
    - "RevisionParser can parse natural language feedback into structured {type, target_shot, instruction} actions"
    - "All agents call ModelRegistry.snapshot() at task start, never get_active()"
    - "All agent operations logged via model_logger.log_model_call()"
    - "Tests pass: `pytest tests/test_agents/ -x -v`"
  artifacts:
    - path: "agents/content_agent.py"
      provides: "Topic divergence, script generation, storyboard generation with dialect injection"
      min_lines: 130
      exports: ["ContentAgent"]
    - path: "agents/production_agent.py"
      provides: "Sequential production pipeline: voice -> DH -> b-roll -> compose"
      min_lines: 100
      exports: ["ProductionAgent"]
    - path: "agents/ops_agent.py"
      provides: "Publish, data collection, weekly report generation"
      min_lines: 80
      exports: ["OpsAgent"]
    - path: "agents/revision_parser.py"
      provides: "Natural language to structured operations via LLMAbstract.chat_json()"
      min_lines: 50
      exports: ["parse_revision"]
    - path: "agents/__init__.py"
      provides: "Clean public API exports"
      exports: ["ContentAgent", "ProductionAgent", "OpsAgent", "parse_revision"]
    - path: "tests/test_agents/conftest.py"
      provides: "Shared fixtures: mock_llm, mock_image_gen, dialect_dict, knowledge_base"
    - path: "tests/test_agents/test_content_agent.py"
      provides: "Tests for ContentAgent: diverge_topics, generate_script, generate_storyboard"
      min_lines: 100
    - path: "tests/test_agents/test_revision_parser.py"
      provides: "Tests for RevisionParser: parse, edge cases, malformed input"
      min_lines: 50
  key_links:
    - from: "agents/content_agent.py"
      to: "services/llm.py LLMAbstract.text_llm"
      via: "import and call chat_json()"
    - from: "agents/content_agent.py"
      to: "services/image_gen.py image_gen.generate_image()"
      via: "call per storyboard shot when need_reference is True"
    - from: "agents/content_agent.py"
      to: "config/model_registry.py ModelRegistry.snapshot()"
      via: "call at task start for model selection freeze"
    - from: "agents/production_agent.py"
      to: "services/voice.py voice.generate_voice()"
      via: "call with text, output_path, job_id"
    - from: "agents/production_agent.py"
      to: "services/composer.py composer.compose_video()"
      via: "asyncio.to_thread() to avoid event loop blocking"
    - from: "agents/ops_agent.py"
      to: "services/publisher.py publisher.publish()"
      via: "call with video_path, meta, platforms"
    - from: "agents/revision_parser.py"
      to: "services/llm.py LLMAbstract.text_llm"
      via: "call chat_json() with REVISION_PARSE_PROMPT"

---
<objective>
Implement all four Agent classes (Content, Production, Operations) and the Revision Parser that together form the autonomous video production pipeline. These agents compose existing Phase 2/3 services (LLMAbstract, voice, digital_human, video_gen, composer, publisher, image_gen, model_logger, ModelRegistry) following the state machine in web/models.py.

**Purpose:** Turn existing service functions into a cohesive pipeline that takes a user idea all the way to a published video with minimal human intervention.

**Output:** Four agent files, updated prompts file, test infrastructure for agent tests, and passing tests.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
<interfaces>

From services/llm.py:
```python
class LLMAbstract:
    def __init__(self, function_id: str = "text_llm"): ...
    async def chat(self, messages: list, **kwargs) -> str: ...
    async def chat_json(self, messages: list, **kwargs) -> dict: ...

# Global instances (importable)
text_llm = LLMAbstract("text_llm")  # For text generation tasks
multimodal_llm = LLMAbstract("multimodal")  # For multimodal tasks
```

From services/image_gen.py:
```python
async def generate_image(prompt: str, output_path: str, job_id: str = "test") -> str: ...
```

From services/voice.py:
```python
async def generate_voice(text: str, output_path: str, job_id: str = "test") -> str: ...
```

From services/digital_human.py:
```python
async def create_digital_human(audio_path: str, output_path: str = None, job_id: str = "test") -> str: ...
```

From services/video_gen.py:
```python
async def generate_broll(prompt: str, output_path: str = None, target_duration: float = 5.0, job_id: str = "test") -> str: ...
```

From services/composer.py:
```python
def compose_video(digital_human_path: str, voice_path: str, b_roll_clips: list[dict], subtitles: list[dict], bgm_path: str, branding_path: str, output_path: str, fmt: str = "9:16") -> str: ...
```

From services/publisher.py:
```python
async def publish(video_path: str, meta: dict, platforms: list[str], job_id: str = "test") -> dict: ...
```

From services/model_logger.py:
```python
class Timer: ...  # Context manager, provides .elapsed_ms
async def log_model_call(job_id: str, task_type: str, model_id: str, provider: str, channel: str = "unknown", input_tokens: int = 0, output_tokens: int = 0, latency_ms: int = 0, cost_estimate: float = 0.0, success: int = 1, error_message: str = None, quality_score: float = None): ...
```

From config/model_registry.py:
```python
class ModelRegistry:
    @classmethod
    def snapshot(cls, function_id: str) -> ModelOption: ...  # Freeze model config at task start
    @classmethod
    def get_active(cls, function_id: str) -> ModelOption: ...  # Live config (NOT for agents)
```

From web/models.py (state machine):
```python
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

From web/database.py:
```python
async def get_db_connection(): ...  # Returns aiosqlite.Connection
```

Existing tests/conftest.py fixture pattern:
```python
@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT
```

</interfaces>

@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/phase4_agent_orchestration/04-RESEARCH.md
@web/models.py
@services/llm.py
@services/model_logger.py
@services/__init__.py
@services/voice.py
@services/digital_human.py
@services/video_gen.py
@services/composer.py
@services/publisher.py
@services/image_gen.py
@config/model_registry.py
@config/prompts.py
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Define agent prompt templates in config/prompts.py</name>
  <files>
    config/prompts.py
  </files>
  <action>
    Append the following prompt template constants and add the ContentAgent prompt constants at module level in `config/prompts.py`. Keep existing DEFAULT_SYSTEM_PROMPT and get_prompt() function. Add new constants:

    1. `TOPIC_DIVERGE_PROMPT` — 提示 LLM 从用户想法发散 3-5 个选题角度。参数：{user_idea}, {dialect_words}。输出 JSON: {"topics": [{"title", "pillar", "hook", "reason"}]}。pillar 取值 food/travel/culture/people/history。
    2. `SCRIPT_GENERATION_PROMPT` — 提示 LLM 生成完整脚本。参数：{topic_title}, {pillar}, {dialect_dict}, {knowledge_base}。要求：嵌入至少 3 个攸县方言词汇，30-45 秒口播稿（150-250 字），开头钩子+干货+互动引导。输出 JSON: {"content", "dialect_words": [{"word", "position"}], "subtitles": [{"start", "end", "text"}]}。
    3. `STORYBOARD_PROMPT` — 提示 LLM 生成分镜列表。参数：{script_content}。每个分镜含 shot_number, type (digital_human/b_roll), visual_description（英文）, duration, need_reference, start_time。输出 JSON: {"shots": [...]}。
    4. `WEEKLY_REPORT_PROMPT` — 提示 LLM 生成周分析报告。参数：{data}。输出 JSON: {"platform_summary": {}, "best_content": "", "recommendations": [], "anomalies": []}。

    Export all constants via a `get_agent_prompt(name: str) -> str` function that returns the constant, or raise ValueError for unknown names. This function is used by agents to access prompts without importing constants directly.
  </action>
  <verify>
    <automated>python3 -c "from config.prompts import get_agent_prompt; p=get_agent_prompt('topic_diverge'); assert '{user_idea}' in p; assert '{dialect_words}' in p; print('OK')"</automated>
  </verify>
  <done>Prompt templates exist with correct parameter placeholders; all output JSON schemas defined.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement ContentAgent</name>
  <files>
    agents/__init__.py
    agents/content_agent.py
  </files>
  <behavior>
    - diverge_topics(user_idea: str) -> list[dict]: calls text_llm.chat_json() with TOPIC_DIVERGE_PROMPT, returns result["topics"]
    - generate_script(topic: dict, video_id: int) -> dict: calls text_llm.chat_json() with SCRIPT_GENERATION_PROMPT using topic["title"], topic["pillar"], dialect_dict, knowledge_base; saves script to DB; updates video status to "script_ready"; returns script dict
    - generate_storyboard(script: dict, video_id: int) -> list[dict]: calls text_llm.chat_json() with STORYBOARD_PROMPT; for each shot where need_reference=True, calls image_gen.generate_image(); saves storyboard to DB; updates video status to "storyboard_ready"; returns shot list
    - _load_dialect_dict() -> dict: reads data/dialect_dict.json
    - _load_knowledge_base() -> str: reads data/knowledge_base.md
    - _update_status(db, video_id, status): executes UPDATE videos SET status=? WHERE id=?
    - ModelRegistry.snapshot("text_llm") called at the start of each public method
    - Each public method wraps LLM call with model_logger.Timer and logs via log_model_call()
  </action>
  <action>
    Create `agents/__init__.py`:
    ```python
    """Agent orchestration package."""
    from agents.content_agent import ContentAgent
    from agents.production_agent import ProductionAgent
    from agents.ops_agent import OpsAgent
    from agents.revision_parser import parse_revision

    __all__ = ["ContentAgent", "ProductionAgent", "OpsAgent", "parse_revision"]
    ```

    Create `agents/content_agent.py`:

    Key implementation rules per research:
    - `text_llm` is imported from `services.llm` (global instance, already initialized with function_id="text_llm")
    - `generate_image` is imported from `services.image_gen`
    - `ModelRegistry.snapshot()` is called at start of each public method (not `get_active()`)
    - Dialect dict loaded from `data/dialect_dict.json` (relative to project root)
    - Knowledge base loaded from `data/knowledge_base.md`
    - Database connection via `get_db_connection()` from `web.database`
    - All LLM calls use `text_llm.chat_json()` for structured JSON output
    - Validate transitions using VALID_TRANSITIONS before updating status
    - Use Timer context manager + log_model_call() for each LLM/image call
    - Prompt constants accessed via `config.prompts.get_agent_prompt(name)`
    - model_logger imported as: `from services.model_logger import log_model_call, Timer`
    - Path resolution: use `Path(__file__).parent.parent` for project root, not os.path

    Structure:
    ```python
    class ContentAgent:
        def __init__(self):
            # Load dialect_dict and knowledge_base from files

        async def diverge_topics(self, user_idea: str) -> list[dict]:
            model = ModelRegistry.snapshot("text_llm")
            # call text_llm.chat_json() with TOPIC_DIVERGE_PROMPT
            # log via Timer + log_model_call
            return result.get("topics", [])

        async def generate_script(self, topic: dict, video_id: int) -> dict:
            model = ModelRegistry.snapshot("text_llm")
            # call text_llm.chat_json() with SCRIPT_GENERATION_PROMPT
            # INSERT into scripts table
            # UPDATE videos status to "script_ready"
            # log model call
            return script

        async def generate_storyboard(self, script: dict, video_id: int) -> list[dict]:
            model = ModelRegistry.snapshot("text_llm")
            # call text_llm.chat_json() with STORYBOARD_PROMPT
            # for shots where need_reference: generate_image()
            # INSERT into storyboards table
            # UPDATE videos status to "storyboard_ready"
            # log model call
            return shot_list
    ```
  </action>
  <verify>
    <automated>pytest tests/test_agents/test_content_agent.py -x -v 2>&1 | head -40</automated>
  </verify>
  <done>ContentAgent.diverge_topics returns topic list; generate_script returns script dict with dialect words; generate_storyboard returns shot list with reference images. All use ModelRegistry.snapshot(), log model calls, and update DB state.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Implement ProductionAgent, OpsAgent, and RevisionParser</name>
  <files>
    agents/production_agent.py
    agents/ops_agent.py
    agents/revision_parser.py
  </files>
  <behavior>
    - ProductionAgent.produce_single(storyboard, video_id): calls voice.generate_voice() -> update status to voice_ready -> create_digital_human() -> avatar_ready -> asyncio.gather() for parallel b-roll generation -> broll_ready -> asyncio.to_thread(composer.compose_video, ...) -> composed
    - OpsAgent.publish_approved(video_id, video_path, platforms, meta): calls publisher.publish()
    - OpsAgent.collect_daily_data(): returns simulated platform data dict
    - OpsAgent.generate_weekly_report(weekly_data): calls text_llm.chat_json() with WEEKLY_REPORT_PROMPT
    - RevisionParser.parse_revision(instruction, video_info): calls text_llm.chat_json() with REVISION_PARSE_PROMPT, returns {"rollback_level": "minor|major|critical", "actions": [...]}
  </action>
  <action>
    Create `agents/production_agent.py`:
    - Import voice, digital_human, video_gen, composer modules directly (they are top-level async functions in services/):
      ```python
      from services import voice, digital_human, video_gen, composer
      from services.model_logger import log_model_call, Timer
      from web.database import get_db_connection
      from web.models import VALID_TRANSITIONS
      ```
    - `composer.compose_video()` is synchronous (FFmpeg subprocess) — MUST wrap in `asyncio.to_thread()` per research pitfall #2
    - B-roll generation uses `asyncio.gather()` for parallel generation across shots with type=="b_roll" — per research anti-pattern avoidance
    - Each step: call service -> log model call -> update status
    - Status updates use VALID_TRANSITIONS dict for validation
    - `_select_bgm(mood: str) -> str`: maps mood to a BGM path under templates/music/
    - Error handling: each step wrapped in try/except, on failure log error and set status to current state (allowing retry from same point) — per research pitfall #2 for async safety
    - Use `project_root = Path(__file__).parent.parent` for resolving bgm/branding paths

    Create `agents/ops_agent.py`:
    ```python
    import json
    from services.publisher import publish
    from services.llm import text_llm
    from services.model_logger import log_model_call, Timer
    from config.model_registry import ModelRegistry
    from config.prompts import get_agent_prompt

    class OpsAgent:
        async def publish_approved(self, video_id: int, video_path: str, platforms: list[str], meta: dict) -> dict:
            model = ModelRegistry.snapshot("text_llm")
            result = await publish(video_path=video_path, meta=meta, platforms=platforms, job_id=str(video_id))
            # log model call
            return result

        async def collect_daily_data(self) -> dict:
            # Simulated: returns {platform: {"status": "simulated", "note": "Data collection stub"}}
            return {p: {"status": "simulated", "note": "Stub"} for p in ["douyin", "kuaishou", "weixin", "xiaohongshu"]}

        async def generate_weekly_report(self, weekly_data: dict) -> dict:
            model = ModelRegistry.snapshot("text_llm")
            prompt = get_agent_prompt("weekly_report").format(data=json.dumps(weekly_data, ensure_ascii=False))
            result = await text_llm.chat_json([{"role": "system", "content": prompt}])
            # log model call
            return result
    ```
    - log_model_call uses "ops" as task_type and model.id/provider from snapshot

    Create `agents/revision_parser.py`:
    ```python
    import json
    from services.llm import text_llm
    from services.model_logger import log_model_call, Timer
    from config.model_registry import ModelRegistry
    from config.prompts import get_agent_prompt

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
        model = ModelRegistry.snapshot("text_llm")
        result = await text_llm.chat_json([
            {"role": "system", "content": REVISION_PARSE_PROMPT.format(
                instruction=instruction,
                video_info=json.dumps(video_info, ensure_ascii=False)
            )}
        ])
        # log model call
        return result
    ```
    - The prompt is defined inline in the file (too specific to be a generic template in prompts.py)
    - log_model_call uses task_type="revision_parse"
  </action>
  <verify>
    <automated>
      python3 -c "
from agents.production_agent import ProductionAgent;
from agents.ops_agent import OpsAgent;
from agents.revision_parser import parse_revision;
import inspect;
assert inspect.iscoroutinefunction(ProductionAgent.produce_single);
assert inspect.iscoroutinefunction(OpsAgent.publish_approved);
assert inspect.iscoroutinefunction(parse_revision);
print('All agent classes importable and async')
      "
    </automated>
  </verify>
  <done>ProductionAgent syncs FFmpeg via asyncio.to_thread(), parallelizes b-roll with asyncio.gather(). OpsAgent delegates to publisher. RevisionParser returns structured operations via LLM.chat_json().</done>
</task>

<task type="auto" tdd="true">
  <name>Task 4: Create test infrastructure and agent tests</name>
  <files>
    tests/test_agents/__init__.py
    tests/test_agents/conftest.py
    tests/test_agents/test_content_agent.py
    tests/test_agents/test_revision_parser.py
  </files>
  <behavior>
    - test_content_agent.py::test_diverge_topics: mock text_llm.chat_json to return topics list, verify ContentAgent.diverge_topics returns parsed list
    - test_content_agent.py::test_generate_script: mock text_llm.chat_json to return script dict, verify DB insert called and status updated
    - test_content_agent.py::test_generate_storyboard: mock text_llm.chat_json + image_gen.generate_image, verify shot list returned with images
    - test_revision_parser.py::test_parse_revision: mock text_llm.chat_json to return structured revision, verify rollback_level and actions present
    - test_revision_parser.py::test_parse_revision_empty: handle edge case where LLM returns empty actions list
  </action>
  <action>
    Create `tests/test_agents/__init__.py` — empty package marker.

    Create `tests/test_agents/conftest.py`:
    ```python
    """Shared fixtures for agent tests."""
    import json
    from pathlib import Path
    import pytest
    from unittest.mock import AsyncMock, MagicMock, patch

    PROJECT_ROOT = Path(__file__).parent.parent.parent

    @pytest.fixture
    def mock_llm():
        """Mock text_llm.chat_json to return configurable responses."""
        with patch("agents.content_agent.text_llm") as mock:
            mock.chat_json = AsyncMock()
            yield mock

    @pytest.fixture
    def mock_image_gen():
        """Mock image_gen.generate_image."""
        with patch("agents.content_agent.generate_image") as mock:
            mock.return_value = "/tmp/test_ref_img.png"
            yield mock

    @pytest.fixture
    def mock_db():
        """Mock database connection for agent DB operations."""
        with patch("agents.content_agent.get_db_connection") as mock:
            conn = AsyncMock()
            conn.execute = AsyncMock()
            conn.commit = AsyncMock()
            mock.return_value = conn
            yield conn

    @pytest.fixture
    def dialect_dict() -> dict:
        path = PROJECT_ROOT / "data" / "dialect_dict.json"
        if path.exists():
            return json.loads(path.read_text())
        return {"version": "1.0", "updated": "2026-05-28", "words": [{"word": "恰饭", "meaning": "吃饭", "example": "你恰饭了冇？", "category": "daily"}]}

    @pytest.fixture
    def knowledge_base() -> str:
        path = PROJECT_ROOT / "data" / "knowledge_base.md"
        if path.exists():
            return path.read_text()
        return "# 攸县知识库\n\n## 美食\n攸县米粉是当地特色。"
    ```

    Create `tests/test_agents/test_content_agent.py`:

    - Mark all with pytest.mark.asyncio
    - Set PROJECT_ROOT based on conftest fixture or class constant
    - Each test patches `ModelRegistry.snapshot` to return a mock ModelOption (use `from config.model_registry import ModelOption`):
      ```python
      from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
      import pytest
      from agents.content_agent import ContentAgent

      @pytest.fixture
      def agent(mock_llm, mock_image_gen, mock_db):
          with patch("agents.content_agent.ModelRegistry.snapshot") as mock_snap:
              mock_option = MagicMock()
              type(mock_option).id = PropertyMock(return_value="deepseek_v4_flash")
              type(mock_option).provider = PropertyMock(return_value="deepseek")
              type(mock_option).channel = PropertyMock(return_value="official")
              mock_snap.return_value = mock_option
              agent = ContentAgent()
              yield agent
      ```

    - `test_diverge_topics`: set mock_llm.chat_json.return_value = {"topics": [{"title": "攸县米粉历史", "pillar": "food", "hook": "你晓得攸县米粉几多年历史不？", "reason": "历史文化话题易传播"}]}; call agent.diverge_topics("攸县米粉"); assert len(topics) == 1; assert topics[0]["title"] == "攸县米粉历史"
    - `test_generate_script`: mock_llm.chat_json.return_value = script dict; call agent.generate_script(topic, video_id=1); assert "content" in result; assert mock_db.execute.called (DB insert and status update)
    - `test_generate_storyboard`: mock_llm.chat_json.return_value = {"shots": [{"shot_number": 1, "type": "digital_human", "visual_description": "A person talking", "duration": 5, "need_reference": False, "start_time": 0}, {"shot_number": 2, "type": "b_roll", "visual_description": "Bowl of rice noodles", "duration": 4, "need_reference": True, "start_time": 5}]}; call agent.generate_storyboard(script, video_id=1); assert len(shots) == 2; assert shots[1]["reference_image"] is not None (image_gen called for shot with need_reference=True)

    Create `tests/test_agents/test_revision_parser.py`:

    - Mark all with pytest.mark.asyncio
    - Patch both text_llm and ModelRegistry.snapshot as above
    - `test_parse_revision`: mock_llm.chat_json.return_value = {"rollback_level": "major", "actions": [{"type": "rewrite_script", "target_shot": 0, "instruction": "重写开头部分"}]}; call parse_revision("开头太长了，重新写一下", {"title": "test"}); assert result["rollback_level"] == "major"; assert len(result["actions"]) == 1
    - `test_parse_revision_empty`: mock_llm.chat_json.return_value = {"rollback_level": "minor", "actions": []}; call parse_revision("改个字幕颜色", {"title": "test"}); assert result["rollback_level"] == "minor"; assert result["actions"] == []

    Run after implementation:
    ```bash
    pytest tests/test_agents/test_content_agent.py tests/test_agents/test_revision_parser.py -x -v
    ```
  </action>
  <verify>
    <automated>pytest tests/test_agents/test_content_agent.py tests/test_agents/test_revision_parser.py -x -v 2>&1 | tail -30</automated>
  </verify>
  <done>All tests pass. test_diverge_topics mocks LLM and verifies topic list. test_generate_script verifies DB insert + status update. test_generate_storyboard verifies shot list with reference images. test_parse_revision verifies structured output with rollback_level and actions.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| user idea/revision input -> ContentAgent/RevisionParser | Untrusted natural language enters LLM prompt context |
| agent code -> database | Status updates and data persistence |
| agent code -> LLM API | Structured JSON generation requests |
| agent code -> external services | Media generation (voice, DH, video) calls |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-04-01 | Tampering | ContentAgent prompt injection via user idea | mitigate | System prompts constrain output to JSON format; no raw user input placed in system context without escaping via f-string formatting |
| T-04-02 | Information Disclosure | Error messages from LLM/API calls | mitigate | model_logger.log_model_call() already strips API key patterns from error messages before DB logging (verified in existing code) |
| T-04-03 | Denial of Service | Unbounded retry loops in agents | mitigate | All service calls use tenacity with stop_after_attempt(3) — no agent-level retry beyond this |
| T-04-04 | Spoofing | Unauthorized status transitions | mitigate | Status updates validated against VALID_TRANSITIONS from web/models.py before execution |
</threat_model>

<verification>
1. `python3 -c "from agents import ContentAgent, ProductionAgent, OpsAgent, parse_revision; print('All exports OK')"`
2. `python3 -c "from config.prompts import get_agent_prompt; assert get_agent_prompt('topic_diverge'); assert get_agent_prompt('script_generation'); assert get_agent_prompt('storyboard'); assert get_agent_prompt('weekly_report'); print('All prompt templates OK')"`
3. `pytest tests/test_agents/ -x -v` — all 5+ tests pass
</verification>

<success_criteria>
1. All 4 agent files created and importable
2. Agent prompt templates defined in config/prompts.py with correct parameter placeholders
3. ContentAgent can diverge topics, generate script, generate storyboard (verified by tests)
4. ProductionAgent orchestrates voice -> DH -> b-roll -> compose with async safety (asyncio.to_thread for composer, asyncio.gather for b-roll)
5. OpsAgent can publish, collect data, generate reports
6. RevisionParser can parse NL instructions into structured operations
7. All operations use ModelRegistry.snapshot(), not get_active()
8. All operations logged via model_logger.log_model_call()
9. Agent tests pass: pytest tests/test_agents/ -x -v
</success_criteria>

<output>
After completion, create `.planning/phases/phase4_agent_orchestration/phase4_agent_orchestration-01-SUMMARY.md`
</output>
