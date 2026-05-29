---
phase: 03-media_services
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - services/__init__.py
  - services/voice.py
  - services/image_gen.py
  - services/digital_human.py
  - services/video_gen.py
  - services/publisher.py
  - services/model_logger.py
  - data/dialect_dict.json
  - data/knowledge_base.md
  - tests/conftest.py
  - tests/test_services/conftest.py
  - tests/test_services/test_voice.py
  - tests/test_services/test_image_gen.py
  - tests/test_services/test_digital_human.py
  - tests/test_services/test_video_gen.py
  - tests/test_services/test_publisher.py
  - tests/test_data.py
autonomous: true
requirements: [SVC-02, SVC-03, SVC-04, SVC-05, SVC-07, DATA-06, DATA-07, CHECK-07]
user_setup:
  - service: playwright
    why: "Browser automation for WeChat/Xiaohongshu publishing"
    env_vars: []
    cli_command: "playwright install chromium"
must_haves:
  truths:
    - "System can generate dialect voiceover audio via MiMo VoiceClone (or mock if no API key)"
    - "System can generate images for covers/references via GPT-image-2 relay (or mock fallback)"
    - "System can produce mock digital human video from static image + audio + Ken Burns"
    - "System can produce mock B-roll video from placeholder images with zoom/pan"
    - "System can dispatch publisher to correct platform handler (Douyin API / WeChat Playwright)"
    - "Dialect dictionary JSON exists with valid word entries"
    - "Knowledge base MD exists with YouXian topic references"
    - "Every model call (voice/image/digital_human/video/publisher) is logged to model_call_logs table"
  artifacts:
    - path: "services/voice.py"
      provides: "Strategy-dispatched voice generation with all providers"
      min_lines: 120
    - path: "services/image_gen.py"
      provides: "Image generation via GPT-image-2 relay + fallbacks"
      min_lines: 80
    - path: "services/digital_human.py"
      provides: "Digital human with mock/local/manual/heygen/tavus/d-id/akool modes"
      min_lines: 150
    - path: "services/video_gen.py"
      provides: "B-roll video generation with mock/local/runway/veo/kling/luma/pika/hailuo modes"
      min_lines: 150
    - path: "services/publisher.py"
      provides: "Multi-platform publishing via Douyin API + WeChat Playwright"
      min_lines: 120
    - path: "services/model_logger.py"
      provides: "Shared model call logging utility"
      min_lines: 40
    - path: "data/dialect_dict.json"
      provides: "Dialect dictionary with word entries"
      min_lines: 10
    - path: "data/knowledge_base.md"
      provides: "YouXian knowledge base for content agent"
      min_lines: 50
  key_links:
    - from: "services/voice.py"
      to: "config/model_registry.py"
      via: "ModelRegistry.snapshot('voice_clone')"
      pattern: "ModelRegistry\\.snapshot\\(\"voice_clone\"\\)"
    - from: "services/image_gen.py"
      to: "config/model_registry.py"
      via: "ModelRegistry.snapshot('image_gen')"
      pattern: "ModelRegistry\\.snapshot\\(\"image_gen\"\\)"
    - from: "services/digital_human.py"
      to: "config/model_registry.py"
      via: "ModelRegistry.snapshot('digital_human')"
      pattern: "ModelRegistry\\.snapshot\\(\"digital_human\"\\)"
    - from: "services/video_gen.py"
      to: "config/model_registry.py"
      via: "ModelRegistry.snapshot('video_gen')"
      pattern: "ModelRegistry\\.snapshot\\(\"video_gen\"\\)"
    - from: "services/model_logger.py"
      to: "web/database.py"
      via: "get_db_connection() for INSERT INTO model_call_logs"
      pattern: "get_db_connection"
    - from: "services/*.py"
      to: "services/model_logger.py"
      via: "log_model_call(...) after each provider invocation"
      pattern: "log_model_call"
    - from: "services/__init__.py"
      to: "services/voice.py"
      via: "get_http_client() shared singleton"
      pattern: "get_http_client"
---

<objective>
Build all media generation services and multi-platform publishing for the YouXian Says system.

Purpose: Implement the complete media pipeline -- voice cloning, digital human, B-roll video, image generation, and multi-platform publishing -- with strategy-pattern dispatch via ModelRegistry.snapshot(). Every service supports mock mode so the pipeline works without paid API keys. All model calls are logged to model_call_logs.

Output: Six service modules (voice, image_gen, digital_human, video_gen, publisher, model_logger), two data files (dialect_dict.json, knowledge_base.md), and test files for all services.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/REQUIREMENTS.md
@.planning/phases/phase3_media_services/03-RESEARCH.md

@services/__init__.py
@services/composer.py
@config/model_registry.py
@web/database.py
@tests/conftest.py

<interfaces>
<!-- Key contracts the executor needs. Extracted from codebase. -->

From config/model_registry.py (existing):
```python
@dataclass
class ModelOption:
    id: str
    name: str
    provider: str
    api_base: str
    model_name: str
    api_key_env: str
    channel: str = "official"
    api_compatibility: str = ""
    resolved_api_key: str = ""
    fallback_ids: list[str] = field(default_factory=list)
    # ... additional fields

class ModelRegistry:
    @classmethod
    def snapshot(cls, function_id: str) -> ModelOption:
        """Task startup snapshot - immune to runtime switches"""
```

From config/model_registry.py (function slots relevant to Phase 3):
- "voice_clone": active_id="mimo_voiceclone", fallback_ids=["mimo_voicedesign","mimo_tts","elevenlabs_tts","cartesia_tts","openai_tts","minimax_speech"]
- "digital_human": active_id="heygen", fallback_ids=["tavus","d_id","akool"]
- "video_gen": active_id="runway_gen4_turbo", fallback_ids=["veo_3_1_lite","veo_3_1_fast","kling","luma_ray","pika","hailuo_2_3"]
- "image_gen": active_id="gpt_image2_relay", fallback_ids=["firefly_image","imagen_4","seedream","flux","minimax_image_01"]

From web/database.py (existing):
```python
async def get_db_connection():
    """Get a direct async connection for scripts."""
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA busy_timeout=5000")
    await db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = aiosqlite.Row
    return db
```

From web/routers/videos.py (existing model_call_logs schema):
```sql
INSERT INTO model_call_logs (job_id, task_type, model_id, provider, channel,
    input_tokens, output_tokens, latency_ms, cost_estimate, success)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```
</interfaces>
</context>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Python service -> External model API | Untrusted model API response enters service logic |
| Playwright browser -> Social platform | User cookies stored locally; platform may detect automation |
| Service -> model_call_logs DB | Local DB -- no external trust boundary |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-03-01 | Information Disclosure | All services when logging errors | mitigate | Strip API keys from error messages before logging; never log raw request bodies containing secrets |
| T-03-02 | Spoofing | publisher.py automated publish | mitigate | MVP requires human confirmation gate (pending_review -> approved); no unattended publish by default |
| T-03-03 | Tampering | publisher.py Playwright cookies | mitigate | Cookies stored as local JSON files; consider encrypting at rest if sensitive |
| T-03-04 | Spoofing | digital_human/video_gen external APIs | accept | API keys are the only auth; no additional verification beyond HTTPS |
| T-03-05 | Information Disclosure | voice/image/video API calls | accept | Model input is public script text; no PII sent to generation models per data_policy |
</threat_model>

<tasks>

<task type="auto">
  <name>Task 1: Create shared model_logger.py and update services/__init__.py with shared httpx client</name>
  <files>
    services/model_logger.py
    services/__init__.py
  </files>
  <action>

Create `services/model_logger.py` as a reusable async utility for logging model calls to the `model_call_logs` table.

- Define an async function `log_model_call(job_id, task_type, model_id, provider, channel, latency_ms, cost_estimate, success, error_message=None, input_tokens=0, output_tokens=0, quality_score=None)`.
- Use `get_db_connection()` from `web/database.py` to get an `aiosqlite` connection.
- Execute `INSERT INTO model_call_logs (job_id, task_type, model_id, provider, channel, input_tokens, output_tokens, latency_ms, cost_estimate, success, error_message, quality_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)` with the provided fields.
- Handle database errors gracefully: log a warning if insert fails, do not raise.

Update `services/__init__.py` to export a shared `get_http_client()` singleton:

- Move the `_shared_client` / `get_http_client()` pattern from the tech spec (section 4.3 code example) into `services/__init__.py`.
- The shared client is an `httpx.AsyncClient` with `timeout=httpx.Timeout(120.0, connect=10.0)` and `limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)`.
- Import and re-export `get_http_client` so all service modules can do `from services import get_http_client`.

Import both in `__init__.py` so they are accessible as `from services import get_http_client, log_model_call`.
</action>
  <verify>
    <automated>python -c "from services import get_http_client, log_model_call; print('OK')"</automated>
  </verify>
  <done>model_logger.py created with log_model_call function; __init__.py exports shared httpx client and logger</done>
</task>

<task type="auto">
  <name>Task 2: Create voice.py with strategy-pattern dispatch and image_gen.py with GPT-image-2 relay + fallbacks</name>
  <files>
    services/voice.py
    services/image_gen.py
    tests/test_services/conftest.py
    tests/test_services/test_voice.py
    tests/test_services/test_image_gen.py
  </files>
  <action>

Create `services/voice.py` (SVC-02). Follow the strategy-pattern dispatch described in the tech spec section 4.3 and RESEARCH.md Pattern 1.

- Define a `VOICE_PROVIDERS` dict mapping model.id prefixes to async provider functions.
- The main entry point is `async def generate_voice(text: str, output_path: str, job_id: str = "test") -> str`.
  - Inside: `model = ModelRegistry.snapshot("voice_clone")`, look up `VOICE_PROVIDERS.get(model.id)`, call the provider function.
  - After the provider returns, call `log_model_call(...)` with the task_type, model_id, provider, channel, latency, etc.
  - If the provider raises, log the failed call with `success=0` and `error_message`, then re-raise.
- Implement provider functions (use the shared `get_http_client()` from `services.__init__`):
  - `_mimo_tts(text, path, model)`: POST to `{model.api_base}/v1/audio/speech`, JSON body `{"model": model.model_name, "text": text, "voice_id": "yuxian_dialect_clone", "format": "wav"}`, header `Authorization: Bearer {model.resolved_api_key}`. Write response content to `path`. Return `path`.
  - `_minimax_tts(text, path, model)`: POST to `{model.api_base}/t2a_v2`, JSON body with Speech-2.8 config from tech spec section 4.3 code example. This is LAST RESORT only -- log a WARNING via `import logging; logger.warning(...)` when called.
  - `_external_tts(text, path, model)`: Generic POST for ElevenLabs/Cartesia/OpenAI TTS; POST to `{model.api_base}/tts` with text.
  - `_mock_tts(text, path, model)`: Generate a silent WAV file using FFmpeg (`anullsrc` filter, 30 seconds). This is called when no API key is available.
- Map providers in `VOICE_PROVIDERS`:
  - "mimo_voiceclone", "mimo_tts", "mimo_voicedesign" -> `_mimo_tts`
  - "minimax_speech" -> `_minimax_tts`
  - "elevenlabs", "cartesia" -> `_external_tts`
  - "openai_tts" -> `_external_tts` (or a dedicated OpenAI TTS handler that uses OpenAI client)
  - "mock" -> `_mock_tts`
- For models not registered in the dict, check `model.fallback_ids` and try the first registered fallback; if none works, use `_mock_tts` as ultimate fallback for development purposes.
- Ensure output path directory is created (`Path(output_path).parent.mkdir(parents=True, exist_ok=True)`).

Create `services/image_gen.py` (SVC-05).

- Define `IMAGE_PROVIDERS` dict mapping model.id prefixes to async provider functions.
- Main entry: `async def generate_image(prompt: str, output_path: str, job_id: str = "test") -> str`.
  - `model = ModelRegistry.snapshot("image_gen")`, dispatch via `IMAGE_PROVIDERS`.
  - Log call via `log_model_call(...)` after provider returns or on failure.
- Provider functions:
  - `_gpt_image2(text, path, model)`: Use `openai.AsyncOpenAI(api_key=model.resolved_api_key, base_url=model.api_base)`, call `client.images.generate(model="gpt-image-2", prompt=text, n=1, size="1792x1024")`. Save the returned image URL content to `path`.
  - `_mock_image(text, path, model)`: Generate a 1x1 pixel PNG placeholder using Python (struct to create minimal PNG), or use PIL/Pillow if installed (but don't require it -- fall back to a text-based placeholder file). Write to `path`.
- `IMAGE_PROVIDERS` mapping:
  - "gpt_image2" -> `_gpt_image2`
  - "mock" -> `_mock_image`
- Fallback: try `model.fallback_ids` for registered providers; ultimately fall back to mock.

Create `tests/test_services/conftest.py` with shared fixtures for service tests:
- `mock_model_option()` fixture: returns a `ModelOption` with mock-friendly defaults.
- `tmp_output_dir(tmp_path)` fixture: returns a temporary directory for generated files.

Create `tests/test_services/test_voice.py`:
- `test_generate_voice_uses_mock_when_no_key`: Uses mock model option, verifies `generate_voice` returns a path.
- `test_voice_provider_dispatch`: Verifies `VOICE_PROVIDERS` has entries for all providers listed in voice_clone FunctionSlot options (mimo_voiceclone, mimo_tts, mimo_voicedesign, minimax_speech, elevenlabs, cartesia, openai_tts).
- `test_model_call_logged_on_voice_generation`: Uses monkeypatch to intercept `log_model_call`, verifies it was called with correct task_type="voice".
- `test_failed_call_logged`: Forces a provider error, verifies `log_model_call` was called with `success=0`.

Create `tests/test_services/test_image_gen.py`:
- `test_generate_image_returns_path`: Calls `generate_image` with mock provider, verifies path returned.
- `test_image_provider_registry`: Verifies `IMAGE_PROVIDERS` has entries for gpt_image2 and mock.
- `test_mock_mode`: Calls `generate_image` with mock provider, verifies output file exists.
</action>
  <verify>
    <automated>python -m pytest tests/test_services/test_voice.py tests/test_services/test_image_gen.py -x -q 2>&1 | tail -5</automated>
  </verify>
  <done>voice.py and image_gen.py created with strategy dispatch; tests pass for both modules</done>
</task>

<task type="auto">
  <name>Task 3: Create digital_human.py, video_gen.py, and publisher.py with all modes</name>
  <files>
    services/digital_human.py
    services/video_gen.py
    services/publisher.py
    tests/test_services/test_digital_human.py
    tests/test_services/test_video_gen.py
    tests/test_services/test_publisher.py
  </files>
  <action>

Create `services/digital_human.py` (SVC-03).

- Define `DIGITAL_HUMAN_PROVIDERS` dict.
- Main entry: `async def create_digital_human(audio_path: str, output_path: str, job_id: str = "test") -> str`.
  - `model = ModelRegistry.snapshot("digital_human")`, dispatch, log.
- Provider functions:
  - `_mock_digital_human(audio_path, output_path, model)`: Use FFmpeg subprocess to create Ken Burns effect on `avatar_placeholder.png` (from `templates/branding/avatar_placeholder.png`) with the audio track. Command pattern (from RESEARCH.md): `ffmpeg -y -loop 1 -i {avatar} -i {audio} -vf "zoompan=z='min(zoom+0.002,1.5)':d=250:s=1080x1920:fps=25" -c:v libx264 -c:a aac -shortest {output}`.
  - `_manual_instructions(audio_path, output_path, model)`: Write a JSON instruction file to `output_path` (with .json extension) containing audio path, text transcript placeholder, avatar style notes, and the message "Manual upload required: use this audio + avatar description to generate in HeyGen/剪映/腾讯智影".
  - `_heygen_video(audio_path, output_path, model)`: POST to `{model.api_base}/v2/video/generate` with avatar_id from env, audio_url (note: real implementation needs a publicly accessible URL; for now use placeholder), dimension 1080x1920. Return task_id string.
  - `_tavus_video`, `_d_id_video`, `_akool_video`: Placeholder implementations that raise `NotImplementedError` with message "{provider} API not yet integrated -- configure API key in settings and implement provider handler".
- "local" mode: same as mock for now (per RESEARCH.md).
- `DIGITAL_HUMAN_PROVIDERS` mapping:
  - "mock", "local" -> `_mock_digital_human`
  - "manual" -> `_manual_instructions`
  - "heygen" -> `_heygen_video`
  - "tavus" -> `_tavus_video`
  - "d_id" -> `_d_id_video`
  - "akool" -> `_akool_video`
- Add fallback logic: if provider raises NotImplementedError and model has fallback_ids, try the first registered fallback.

Create `services/video_gen.py` (SVC-04).

- Define `VIDEO_PROVIDERS` dict.
- Main entry: `async def generate_broll(prompt: str, output_path: str, target_duration: float = 5.0, job_id: str = "test") -> str`.
  - `model = ModelRegistry.snapshot("video_gen")`, dispatch, log.
- Provider functions:
  - `_mock_broll(prompt, output_path, duration, model)`: Use FFmpeg to create a Ken Burns zoom effect on `broll_placeholder.png` for `duration` seconds at 1080x1920. Command: `ffmpeg -y -loop 1 -i {broll_img} -vf "zoompan=z='min(zoom+0.003,1.5)':d={int(duration*25)}:s=1080x1920:fps=25" -c:v libx264 -t {duration} -pix_fmt yuv420p {output}`.
  - For long durations (>6s), generate multiple clips and concatenate them (addressed per Pitfall 5 from RESEARCH.md).
  - `_runway_video`, `_veo_video`, `_kling_video`, `_luma_video`, `_pika_video`, `_hailuo_video`: Placeholder implementations raising `NotImplementedError` with provider name.
- `VIDEO_PROVIDERS` mapping:
  - "mock", "local" -> `_mock_broll`
  - "runway" -> `_runway_video`
  - "veo" -> `_veo_video`
  - "kling" -> `_kling_video`
  - "luma" -> `_luma_video`
  - "pika" -> `_pika_video`
  - "hailuo" -> `_hailuo_video`
- fallback: try model.fallback_ids for registered providers; ultimately fall back to mock.

Create `services/publisher.py` (SVC-07).

- Define `OFFICIAL_API_PLATFORMS = ["douyin", "kuaishou"]` and `BROWSER_PLATFORMS = ["weixin", "xiaohongshu"]`.
- Define `PLATFORM_PROVIDERS` dict mapping platform name to async handler function.
- Main entry: `async def publish(video_path: str, meta: dict, platforms: list[str], job_id: str = "test") -> dict`.
  - For each platform, dispatch to the handler, log the call via `log_model_call`.
  - Return `{platform: result_dict}` for all platforms.
- Handler functions:
  - `_douyin_api(video_path, meta, model)`: Attempt POST to Douyin open API. For now, return `{"status": "simulated", "message": "Douyin API call simulated -- configure API credentials for production"}`.
  - `_kuaishou_api(video_path, meta, model)`: Same simulated pattern.
  - `_weixin_playwright(video_path, meta, model)`: Playwright flow (browser setup pseudocode for now):
    ```python
    async def _weixin_playwright(video_path, meta, model):
        """Publish to WeChat Channels via Playwright automation.
        Note: Requires saved cookies with valid session."""
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            # Load cookies if exists
            cookie_file = Path("data/cookies_weixin.json")
            if cookie_file.exists():
                import json
                cookies = json.loads(cookie_file.read_text())
                await context.add_cookies(cookies)
            page = await context.new_page()
            await page.goto("https://channels.weixin.qq.com/")
            # Check login state
            login_ok = await page.locator(".user-avatar").count() > 0
            if not login_ok:
                return {"status": "cookie_expired", "message": "WeChat session expired -- please re-authenticate manually"}
            # Navigate to publish page
            await page.goto("https://channels.weixin.qq.com/publish")
            # Upload video (platform-specific file input)
            # ... (detailed implementation deferred to integration phase)
            await browser.close()
            return {"status": "simulated", "platform": "weixin", "note": "Playwright flow requires cookie setup and manual first-time auth"}
    ```
  - `_xiaohongshu_playwright(video_path, meta, model)`: Same pattern as weixin above with xiaohongshu URLs.
- Return simulated results for all platforms for now (per the "ship first, buy later" philosophy -- actual credential integration happens after cookies/API keys are configured).

Create `tests/test_services/test_digital_human.py`:
- `test_mock_mode_creates_mp4`: Calls `create_digital_human` with a mock model option, verifies output path ends with `.mp4`.
- `test_all_modes_registered`: Verifies `DIGITAL_HUMAN_PROVIDERS` has entries for mock, local, manual, heygen, tavus, d_id, akool.
- `test_manual_mode_returns_json`: Calls with manual mode, verifies output path ends with `.json` and file is valid JSON.

Create `tests/test_services/test_video_gen.py`:
- `test_mock_mode_creates_mp4`: Calls `generate_broll` with mock provider, verifies output exists.
- `test_provider_registry`: Verifies VIDEO_PROVIDERS has all required entries.
- `test_long_duration_splits`: Calls with target_duration > 10s, verifies fallback to mock.

Create `tests/test_services/test_publisher.py`:
- `test_platform_dispatch`: Calls `publish` with `platforms=["douyin", "weixin"]`, verifies result dict has both keys.
- `test_offical_api_simulated`: Verifies douyin handler returns simulated status.
- `test_all_platforms_registered`: Verifies PLATFORM_PROVIDERS has entries for douyin, kuaishou, weixin, xiaohongshu.
</action>
  <verify>
    <automated>python -m pytest tests/test_services/test_digital_human.py tests/test_services/test_video_gen.py tests/test_services/test_publisher.py -x -q 2>&1 | tail -5</automated>
  </verify>
  <done>digital_human.py, video_gen.py, publisher.py created with all modes; all service tests pass</done>
</task>

<task type="auto">
  <name>Task 4: Create dialect_dict.json, knowledge_base.md, and data format tests</name>
  <files>
    data/dialect_dict.json
    data/knowledge_base.md
    tests/test_data.py
  </files>
  <action>

Create `data/dialect_dict.json` (DATA-06). This is a JSON file mapping YouXian dialect words to their meanings, pinyin, and usage examples. Include at least 20 entries covering common dialect terms.

Schema:
```json
{
  "version": "1.0",
  "updated": "2026-05-28",
  "words": [
    {
      "word": "恰饭",
      "pinyin": "qia fan",
      "meaning": "吃饭",
      "example": "你恰饭了冇？",
      "category": "daily_life"
    }
  ]
}
```

Include entries for: 恰饭, 耍, 冇, 咯, 哩, 崽, 妹几, 老子, 何解, 嗯咯, 好多, 几多, 哈, 喽, 咯哩咯嗦, 醒门子, 弹四郎, 扯卵谈, 冇得, 跟哒, 何什.

Create `data/knowledge_base.md` (DATA-07). Include sections about YouXian topics that the content agent can use for script generation. Sections should cover:
- 攸县概况 (geography, population, history)
- 攸县方言特点 (phonetic features, common expressions)
- 攸县特色美食 (rice noodles, tofu, etc.)
- 攸县风俗习惯 (festivals, traditions)
- 攸县旅游景点 (cultural sites, natural attractions)
- 攸县知名人物
- 热点话题和短视频趋势

Each section should have 3-5 bullet points with factual information. The knowledge base should be informative enough for the content agent to generate accurate, localized scripts.

Create `tests/test_data.py`:
- `test_dialect_dict_exists`: Verifies `data/dialect_dict.json` exists and is valid JSON.
- `test_dialect_dict_schema`: Verifies the JSON has `version`, `updated`, `words` keys, and each word entry has `word`, `meaning`, and `example` fields.
- `test_dialect_dict_min_entries`: Verifies at least 20 word entries.
- `test_knowledge_base_exists`: Verifies `data/knowledge_base.md` exists.
- `test_knowledge_base_sections`: Verifies it contains at least 4 of the required section headings (starting with ##).
- `test_knowledge_base_min_length`: Verifies at least 50 lines of content.
</action>
  <verify>
    <automated>python -m pytest tests/test_data.py -x -q 2>&1 | tail -5</automated>
  </verify>
  <done>dialect_dict.json with 20+ entries and knowledge_base.md created; data format tests pass</done>
</task>

</tasks>

<verification>
**Per-plan verification:**
1. `python -c "from services import get_http_client, log_model_call; print('imports OK')"` -- verifies shared infrastructure
2. `python -m pytest tests/test_services/ -x -q` -- all service tests pass
3. `python -m pytest tests/test_data.py -x -q` -- data format tests pass
4. Verify `provider_fn = VOICE_PROVIDERS.get(model.id)` pattern is used (not hardcoded if-elif chain for dispatch)
5. Verify no MiniMax model is set as default active_id in any provider -- MiniMax providers are registered but only reached through fallback chain
6. Verify all service modules import and use `get_http_client` from `services.__init__` (not creating their own clients)
7. Verify all service modules call `log_model_call` after each provider invocation, including on failure
</verification>

<success_criteria>
1. `services/voice.py` generates a WAV file when called with any provider (including mock)
2. `services/image_gen.py` generates an image file when called with any provider (including mock)
3. `services/digital_human.py` generates an MP4 (or JSON for manual) file for any mode
4. `services/video_gen.py` generates an MP4 file for mock mode
5. `services/publisher.py` returns result dict for all 4 platforms
6. `services/model_logger.py` successfully inserts into model_call_logs table
7. `data/dialect_dict.json` passes format validation (20+ entries, valid schema)
8. `data/knowledge_base.md` passes format validation (4+ sections, 50+ lines)
9. All 7 test files pass in sequence: `python -m pytest tests/test_services/ tests/test_data.py -x -q`
10. The shared `get_http_client()` is the single httpx client used by all services (grep confirms no duplicate creation)
</success_criteria>

<output>
After completion, create `.planning/phases/phase3_media_services/03-01-SUMMARY.md`
</output>
