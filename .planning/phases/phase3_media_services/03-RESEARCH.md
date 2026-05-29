# Phase 3: Media Services - Research

**Researched:** 2026-05-28
**Domain:** Voice services (TTS/clone), digital human video, B-roll video generation, image generation, multi-platform publishing, dialect dictionary, knowledge base, model call logging
**Confidence:** HIGH (stack), MEDIUM (publisher-specific API details)

## Summary

Phase 3 builds all media generation services and multi-platform publishing capabilities for the YouXian Says system. The architecture follows a strategy pattern: each service module (voice, digital_human, video_gen, image_gen, publisher) receives the current active model config via `ModelRegistry.snapshot()` and dispatches to the appropriate provider implementation. Every service must support mock/local modes that work without paid API keys, as per the project's "ship first, buy later" philosophy.

The voice service uses MiMo VoiceClone as P0 production path, with ElevenLabs/Cartesia/OpenAI TTS as external evaluation candidates, and MiniMax Speech as last-resort baseline. Digital human supports mock (static image + Ken Burns), local (placeholder), manual (upload instructions), heygen (API), tavus/d-id/akool (fallbacks). B-roll supports mock (image Ken Burns), local (local clips), and async-task APIs (runway/veo/kling/luma/pika/hailuo). Image generation relays through GPT-image-2 via OpenAI-compatible responses API. Publisher uses Douyin/Kuaishou official APIs and WeChat/Xiaohongshu via Playwright automation.

All model calls must log to the `model_call_logs` table defined in Phase 2. The `composer.py` service (from Phase 1) handles FFmpeg composition and is called by the production agent after media generation.

**Primary recommendation:** Implement each service as a provider-dispatch module matching the `services/voice.py` pattern from the tech spec, with one shared `get_http_client()` for httpx connection reuse, and `ModelRegistry.snapshot("function_id")` for runtime model routing.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Voice TTS/clone generation | **services/voice.py** | ModelRegistry (model selection) | Strategy pattern: gets active model from registry, dispatches to provider implementation |
| Digital human video | **services/digital_human.py** | ModelRegistry (model selection) | Supports mock/local/manual/heygen/tavus/d-id/akool — all dispatched by provider_id |
| B-roll video generation | **services/video_gen.py** | ModelRegistry (model selection) | Supports mock/local/runway/veo/kling/luma/pika/hailuo — async task polling |
| Image generation | **services/image_gen.py** | ModelRegistry (model selection) | GPT-image-2 relay via OpenAI responses API, fallback chain |
| Video composition | **services/composer.py** | FFmpeg CLI | Already exists in Phase 1; called after all media is generated |
| Multi-platform publishing | **services/publisher.py** | Playwright (browser fallback) | Douyin/Kuaishou use official API; WeChat/Xiaohongshu use Playwright automation |
| Dialect dictionary | **data/dialect_dict.json** | Scripts/LLM (generation) | Static JSON consumed by content agent and voice service for dialect tuning |
| Knowledge base | **data/knowledge_base.md** | Scripts/LLM (generation) | Markdown file consumed by content agent for topic/research context |
| Model call logging | **All service modules** | Database (model_call_logs table) | Every model call records job_id, task_type, model_id, provider, channel, latency, cost |
| Object storage | **External (future)** | Local filesystem (now) | HeyGen/Runway need accessible URLs; Phase 3 uses local filesystem, storage integration deferred |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.28.1 | Async HTTP client | Shared `get_http_client()` for all media service API calls; connection pooling [VERIFIED: venv] |
| openai | 2.38.0 | OpenAI-compatible API client | GPT-image-2 relay via responses API; also used for OpenAI TTS [VERIFIED: venv] |
| playwright | 1.60.0 | Browser automation | Publisher module: WeChat Channels / Xiaohongshu video upload via Playwright [VERIFIED: venv + CLI] |
| tenacity | 9.1.4 | Retry library | All async task (video gen, digital human) polling loops use tenacity retry [VERIFIED: venv] |
| pydantic | 2.13.4 | Data validation | Used for response models, settings, and publish meta validation [VERIFIED: venv] |
| aiosqlite | 0.22.1 | Async SQLite driver | model_call_logs insert from async services [VERIFIED: venv] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| elevenlabs | latest | ElevenLabs Python SDK | External voice eval path (P1); provides `AsyncElevenLabs` client [CITED: Context7 /elevenlabs/elevenlabs-python] |
| pydantic-settings | 2.14.1 | Config management | Already in Phase 2; settings.py reads all API keys from .env [VERIFIED: venv] |
| ffmpeg-python | latest | FFmpeg Python bindings | composer.py already uses subprocess directly; optional wrapper [ASSUMED] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx shared client | Separate aiohttp sessions | httpx is already installed; shared client reduces connection overhead [VERIFIED: venv] |
| ElevenLabs Python SDK | Raw httpx POST | SDK provides typed responses and async methods; raw httpx is fine for uniformity [CITED: Context7 docs] |
| Playwright | Selenium | Playwright is already installed (Phase 2), faster, better async support [VERIFIED: venv] |
| Manual dispatch via if/elif | Provider registry dict | Dict dispatch is cleaner and matches tech spec pattern [CITED: tech spec section 4.3] |

**Installation (additions to requirements.txt):**
```bash
# Already in requirements.txt:
httpx
tenacity
playwright

# Add for ElevenLabs evaluation path (optional):
elevenlabs
```

**Version verification:**
```bash
# Verified 2026-05-28:
pip install httpx       # -> 0.28.1
pip install playwright  # -> 1.60.0
pip install openai      # -> 2.38.0
pip install tenacity    # -> 9.1.4
```

## Architecture Patterns

### System Architecture Diagram

```
[Production Agent (agents/production_agent.py)]
         |
         |--- ModelRegistry.snapshot() ----> [config/model_registry.py]
         |
    [Dispatcher by function_id]
         |
    +----+----+----+----+----+
    |    |    |    |    |    |
    v    v    v    v    v    v
[voice] [digital_human] [video_gen] [image_gen] [composer] [publisher]
  |        |              |            |            |           |
  | httpx  | httpx        | httpx      | openai     | FFmpeg    | httpx / Playwright
  | shared | shared       | shared     | client     | subprocess|
  | client | client       | client     |            |           |
  |        |              |            |            |           |
  v        v              v            v            v           v
[audio]  [avatar video] [B-roll clips] [images]  [final mp4] [published]
  |        |              |            |            |           |
  +--------+--------------+------------+------------+           |
  |                                                            |
  v                                                            v
[model_call_logs table]                              [publish_queue table]
  (every call logged)                                  (status tracking)
```

### Service Flow: Single Video Production

```
1. production_agent.produce_single(script)
   |
2. voice.generate(text, script.id) -> output/voices/{id}.wav
   |  ModelRegistry.snapshot("voice_clone") -> dispatch provider
   |  Log: INSERT INTO model_call_logs (task_type="voice", ...)
   |
3. digital_human.create(audio_path, script) -> avatar_video_path
   |  ModelRegistry.snapshot("digital_human") -> dispatch mode
   |  Log: INSERT INTO model_call_logs (task_type="digital_human", ...)
   |
4. video_gen.generate_broll(shots) -> [broll_clips...]
   |  ModelRegistry.snapshot("video_gen") -> dispatch provider
   |  Log: INSERT INTO model_call_logs for each clip
   |
5. image_gen.generate(cover_description) -> cover.jpg
   |  ModelRegistry.snapshot("image_gen") -> dispatch provider  
   |  Log: INSERT INTO model_call_logs
   |
6. composer.compose_video(dh, voice, broll, subtitles, bgm, branding, output)
   |  FFmpeg subprocess, no model call log needed
   |
7. publisher.publish(output_video, meta, platforms)
   |  Douyin/Kuaishou: API call -> Log
   |  WeChat/Xiaohongshu: Playwright -> Log
```

### Recommended Project Structure (additions from existing)

```

├── config/
│   ├── settings.py              # Existing: all API keys
│   └── model_registry.py        # Existing: voice_clone, digital_human, video_gen, image_gen slots
├── services/
│   ├── __init__.py
│   ├── llm.py                   # Existing
│   ├── composer.py              # Existing
│   ├── voice.py                 # NEW: voice generation with strategy pattern
│   ├── digital_human.py         # NEW: digital human modes
│   ├── video_gen.py             # NEW: B-roll generation
│   ├── image_gen.py             # NEW: image generation
│   ├── publisher.py             # NEW: multi-platform publishing
│   └── model_logger.py          # NEW: shared model call logging utility
├── data/
│   ├── dialect_dict.json         # NEW: dialect dictionary
│   └── knowledge_base.md         # NEW: YouXian knowledge base
├── output/
│   ├── voices/                  # Generated voice files
│   ├── videos/                  # Generated B-roll/avatar files
│   ├── images/                  # Generated images
│   └── final/                   # Final composed videos
```

### Pattern 1: Strategy Dispatch via Provider Registry

**What:** Each service module defines a `PROVIDERS` dict mapping provider IDs to handler functions. `ModelRegistry.snapshot()` returns the current active model config; the service looks up the handler by `model.id` prefix or `model.provider`.

**When to use:** ALL media service modules (voice, digital_human, video_gen, image_gen).

**Example:**
```python
# services/voice.py (pattern from tech spec section 4.3)
import httpx
from config.model_registry import ModelRegistry

_shared_client: httpx.AsyncClient | None = None

async def get_http_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _shared_client

async def _mimo_tts(text, path, model):
    client = await get_http_client()
    resp = await client.post(
        f"{model.api_base}/v1/audio/speech",
        json={"model": model.model_name, "text": text, "format": "wav"},
        headers={"Authorization": f"Bearer {model.resolved_api_key}"},
        timeout=60,
    )
    Path(path).write_bytes(resp.content)
    return path

async def _minimax_speech(text, path, model):
    client = await get_http_client()
    resp = await client.post(f"{model.api_base}/t2a_v2", json={...}, headers={...})
    Path(path).write_bytes(resp.content)
    return path

PROVIDERS = {
    "mimo_voiceclone": _mimo_tts,
    "mimo_tts": _mimo_tts,
    "mimo_voicedesign": _mimo_tts,
    "minimax_speech": _minimax_speech,
    "elevenlabs": _external_tts,
    "cartesia": _external_tts,
}

async def generate_voice(text: str, output_path: str) -> str:
    model = ModelRegistry.snapshot("voice_clone")
    provider_fn = PROVIDERS.get(model.id)
    if not provider_fn:
        raise ValueError(f"Unsupported voice model: {model.id}")
    return await provider_fn(text, output_path, model)
```
[CITED: tech spec section 4.3 - services/voice.py provider dispatch]

### Pattern 2: Async Task Polling for Video/Digital Human

**What:** Providers like HeyGen, Runway, Veo use async task APIs: submit task, get task_id, poll for completion. Use `tenacity` retry with longer intervals for polling.

**When to use:** ALL video generation (digital_human, video_gen) when using remote API providers (not mock/local).

**Example:**
```python
# services/digital_human.py (pattern from tech spec section 4.3)
from tenacity import retry, stop_after_attempt, wait_exponential

async def create_heygen_video(audio_url: str, avatar_id: str, model) -> str:
    client = await get_http_client()
    resp = await client.post(
        f"{model.api_base}/v2/video/generate",
        headers={"X-Api-Key": model.resolved_api_key},
        json={
            "video_inputs": [{
                "character": {"type": "avatar", "avatar_id": avatar_id, "avatar_style": "normal"},
                "voice": {"type": "audio", "audio_url": audio_url},
            }],
            "dimension": {"width": 1080, "height": 1920},
        },
        timeout=30,
    )
    return resp.json()["data"]["video_id"]

async def poll_video_status(video_id: str, model) -> dict:
    client = await get_http_client()
    resp = await client.get(
        f"{model.api_base}/v1/video_status.get?video_id={video_id}",
        headers={"X-Api-Key": model.resolved_api_key},
    )
    data = resp.json()["data"]
    return {"status": data["status"], "video_url": data.get("video_url")}
```
[CITED: Context7 docs - HeyGen API video generation + status polling; tech spec section 4.3]

### Pattern 3: Mock/Local Fallback Chain

**What:** Each media service must provide a mock mode that generates output without any paid API key. Mock digital human: Ken Burns effect on static avatar image + audio. Mock B-roll: Ken Burns on reference images with zoom/pan.

**When to use:** ALWAYS during development; used automatically when no API key is configured for the active model.

**Example:**
```python
# services/digital_human.py — mock mode
async def _mock_digital_human(audio_path: str, model) -> str:
    """Generate mock avatar video: static image + Ken Burns effect + audio."""
    output_path = f"output/videos/mock_avatar_{uuid.uuid4().hex[:8]}.mp4"
    # Use FFmpeg subprocess to create a zoom-pan video from avatar image
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", AVATAR_PLACEHOLDER_PATH,
        "-i", audio_path,
        "-vf", "zoompan=z='min(zoom+0.002,1.5)':d=250:s=1080x1920:fps=25",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        output_path,
    ], check=True, capture_output=True)
    return output_path

PROVIDERS = {
    "mock": _mock_digital_human,
    "local": _mock_digital_human,   # local = same as mock for now
    "manual": _manual_instructions,  # output instruction text
    "heygen": _create_heygen_video,
    "tavus": _tavus_video,
    "d_id": _d_id_video,
    "akool": _akool_video,
}
```
[CITED: tech spec section 4.2.1 - mock/local/manual modes]

### Pattern 4: Model Call Logging Decorator/Utility

**What:** Every model call must log to `model_call_logs` table. Create a utility function that wraps the logging pattern.

**When to use:** ALL service modules before/after every provider call.

**Example:**
```python
# services/model_logger.py
import time
from web.database import get_db_connection

async def log_model_call(
    job_id: str,
    task_type: str,
    model_id: str,
    provider: str,
    channel: str,
    success: bool,
    latency_ms: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_estimate: float = 0.0,
    error_message: str = None,
    quality_score: float = None,
):
    db = await get_db_connection()
    try:
        await db.execute(
            """INSERT INTO model_call_logs
               (job_id, task_type, model_id, provider, channel,
                input_tokens, output_tokens, latency_ms, cost_estimate,
                success, error_message, quality_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job_id, task_type, model_id, provider, channel,
             input_tokens, output_tokens, latency_ms, cost_estimate,
             1 if success else 0, error_message, quality_score),
        )
        await db.commit()
    finally:
        await db.close()
```
[CITED: tech spec section 4.6.4 - model_call_logs table schema]

### Anti-Patterns to Avoid

- **Hardcoding provider logic inside producer agent:** Services must be self-contained dispatch modules. The production agent calls `voice.generate()` not `mimo_tts(...)`. Provider selection is the service's job via ModelRegistry.
- **Creating a new httpx client per request:** Use the shared `get_http_client()` singleton. Repeated client creation wastes connections and slows down async operations.
- **Blocking the event loop with sync HTTP calls:** Use httpx async exclusively. Do NOT use `requests` library in any service module.
- **Not logging failed calls:** Even failed model calls must be logged with `success=0` and `error_message`. This is required for the eval_models.py橫评 script.
- **Hardcoding MiniMax as default:** MiniMax models must NEVER be the default active_id in production paths. They are last-resort baselines only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async HTTP client connection pool | Raw `asyncio.open_connection` | `httpx.AsyncClient` with shared singleton | Connection reuse, timeout management, limits [VERIFIED: venv] |
| Browser automation for publishing | Selenium or custom headless | `playwright.async_api` | Already installed (Phase 2); best-in-class async API [VERIFIED: venv] |
| Retry with backoff for async APIs | Manual try/except/sleep loops | `tenacity.retry` | Exponential backoff, stop conditions, clean syntax [VERIFIED: venv] |
| OpenAI API client | Manual HTTP requests for GPT-image-2 | `openai.AsyncOpenAI` with responses API | Already installed; handles auth, streaming, typing [VERIFIED: venv] |
| Video composition with FFmpeg | Python video libraries (moviepy, etc.) | `subprocess.run()` with FFmpeg | composer.py already exists; FFmpeg handles complex filter chains [VERIFIED: system install + composer.py] |

**Key insight:** The tech spec and Phase 2 already provide all the infrastructure needed. Phase 3 is "fill in the service modules" — do not add new frameworks or dependencies. The only potential addition is `elevenlabs` Python SDK for the external voice evaluation path (P1).

## Common Pitfalls

### Pitfall 1: Async Task API Polling Without Proper Timeouts

**What goes wrong:** Digital human/B-roll generation via HeyGen/Runway can take 5-30 minutes. A polling loop with no timeout blocks the task indefinitely.

**Why it happens:** Async task APIs return `task_id` immediately but the video may take minutes to generate. Code that polls every 5 seconds with no max duration can hang.

**How to avoid:** Set a maximum polling duration (e.g., 30 minutes for HeyGen, 15 for Runway) and fail after timeout. Use `asyncio.wait_for()` or track elapsed time manually.

**Warning signs:** Tasks stuck in "processing" status for hours; no error recovery path.

### Pitfall 2: Playwright Cookie Expiry for Automated Publishing

**What goes wrong:** Saved cookies for WeChat/Xiaohongshu expire after days/weeks. Automated publish fails silently or requires re-login.

**Why it happens:** Social platform cookies include session tokens with limited lifetimes. The publisher loads saved cookies without checking validity.

**How to avoid:** Validate cookies before publish: navigate to a simple page and check if login state is recognized. If expired, notify user to re-authenticate. Implement a cookie refresh mechanism.

**Warning signs:** Publish status shows "success" but video never appears; or Playwright screenshot shows login page.

### Pitfall 3: GPT-image-2 API Compatibility via Relay

**What goes wrong:** GPT-image-2 uses the newer `responses` API (`POST /v1/responses`), not `chat.completions`. A New API relay may not support the responses endpoint correctly.

**Why it happens:** The relay is configured for OpenAI Chat Completions compatibility. GPT-image-2 requires the Responses API format, which is a different endpoint with different parameters.

**How to avoid:** Verify the relay supports `POST /v1/responses` with the `gpt-image-2` model. Check the `api_compatibility` field in ModelOption (`openai_responses`). If the relay does not support it, fall back to a direct OpenAI API key or use an alternative image model.

**Warning signs:** Image generation returns 404 or "unknown endpoint"; model_call_logs show consistent failures for image tasks.

### Pitfall 4: MiMo VoiceClone API Parameters Unknown

**What goes wrong:** The tech spec assumes `model.api_base + "/v1/audio/speech"` for MiMo TTS, but the actual MiMo VoiceClone endpoint and parameters may differ.

**Why it happens:** MiMo documentation is not publicly accessible (`platform.xiaomimimo.com` cannot be fetched). The exact API signature is assumed from the tech spec examples.

**How to avoid:** Make the MiMo provider function configurable — define the endpoint path and parameters in model notes or as model-level config overrides. Start with the assumed endpoint, but log failures to diagnose.

**Warning signs:** 404 or 401 from MiMo API; voice generation consistently fails.

### Pitfall 5: B-roll Video Duration Mismatch

**What goes wrong:** Generated B-roll clips are shorter than the script segment they should cover. The composer has nothing to overlay for remaining duration.

**Why it happens:** Video generation APIs have fixed maximum durations (e.g., Hailuo 6s, Runway Gen-4 Turbo 5-10s). A 30-second segment cannot be covered by a single B-roll generation.

**How to avoid:** For long segments, generate multiple clips sequentially and concatenate them. The video_gen service should accept a target duration and internally split into multiple generation requests if needed.

**Warning signs:** Composed video has black frames or frozen last frame where B-roll was supposed to play.

### Pitfall 6: Ignoring MiniMax "Last Resort" Constraint

**What goes wrong:** Code defaults to MiniMax when other providers error, even if the MiniMax model config is not set up for production quality or requires different API parameters.

**Why it happens:** Developers add MiniMax as a "catch-all" fallback because it's already purchased. This violates the architecture decision that MiniMax is baseline/兜底 only.

**How to avoid:** In fallback chains, MiniMax must be the LAST option. Before falling back to MiniMax, try other external candidates first. Log a WARNING when MiniMax is actually invoked.

**Warning signs:** Production videos consistently use MiniMax; model_call_logs show MiniMax as dominant provider.

## Code Examples

### Shared HTTP Client (services/voice.py)
```python
import httpx

_shared_client: httpx.AsyncClient | None = None

async def get_http_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _shared_client
```
[CITED: tech spec section 4.3]

### Model Call Logging (services/model_logger.py)
```python
import time
from web.database import get_db_connection

async def log_model_call(job_id, task_type, model_id, provider, channel,
                          latency_ms, cost_estimate, success, error_message=None,
                          input_tokens=0, output_tokens=0, quality_score=None):
    db = await get_db_connection()
    try:
        await db.execute(
            """INSERT INTO model_call_logs
               (job_id, task_type, model_id, provider, channel,
                input_tokens, output_tokens, latency_ms, cost_estimate,
                success, error_message, quality_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job_id, task_type, model_id, provider, channel,
             input_tokens, output_tokens, latency_ms, cost_estimate,
             1 if success else 0, error_message, quality_score),
        )
        await db.commit()
    finally:
        await db.close()
```
[CITED: tech spec section 4.6.4]

### HeyGen Video Generation (services/digital_human.py)
```python
async def create_heygen_video(audio_url: str, avatar_id: str, model) -> str:
    client = await get_http_client()
    resp = await client.post(
        f"https://api.heygen.com/v2/video/generate",
        headers={"X-Api-Key": model.resolved_api_key},
        json={
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "audio",
                    "audio_url": audio_url,
                },
            }],
            "dimension": {"width": 1080, "height": 1920},
        },
        timeout=30,
    )
    return resp.json()["data"]["video_id"]
```
[CITED: Context7 docs - HeyGen API /v2/video/generate]

### Publisher Douyin API Flow (services/publisher.py)
```python
OFFICIAL_API_PLATFORMS = ["douyin", "kuaishou"]
BROWSER_PLATFORMS = ["weixin", "xiaohongshu"]

class MultiPlatformPublisher:
    async def publish(self, video_path: str, meta: dict, platforms: list[str]) -> dict:
        results = {}
        for platform in platforms:
            try:
                if platform in OFFICIAL_API_PLATFORMS:
                    results[platform] = await self._publish_via_api(platform, video_path, meta)
                else:
                    results[platform] = await self._publish_via_browser(platform, video_path, meta)
            except Exception as e:
                results[platform] = {"status": "failed", "error": str(e)}
        return results

    async def _publish_via_browser(self, platform, video_path, meta):
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            cookies = self._load_cookies(platform)
            if cookies:
                await page.context.add_cookies(cookies)
            # Platform-specific publish flow
            ...
            await browser.close()
```
[CITED: tech spec section 4.7 - publisher architecture]

### Mock Digital Human (services/digital_human.py)
```python
import subprocess, uuid
from pathlib import Path

AVATAR_PLACEHOLDER = Path(__file__).parent.parent / "templates" / "branding" / "avatar_placeholder.png"

async def _mock_digital_human(audio_path: str, model) -> str:
    output = f"output/videos/mock_avatar_{uuid.uuid4().hex[:8]}.mp4"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(AVATAR_PLACEHOLDER),
        "-i", audio_path,
        "-vf", "zoompan=z='min(zoom+0.002,1.5)':d=250:s=1080x1920:fps=25",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        output,
    ], check=True, capture_output=True)
    return output
```
[CITED: tech spec section 4.2.1 - mock mode behavior]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MiniMax as default voice/video | MiMo voice first, Runway/etc for video, MiniMax last baseline | 2026-05-28 review | All default active_ids changed; MiniMax removed from production path |
| Hardcoded provider selection | ModelRegistry.snapshot() runtime dispatch | Phase 1-2 | Services never hardcode provider logic |
| Sync HTTP calls (requests) | Async httpx with shared client | Phase 2 | All services use async exclusively |
| MiniMax image-01 as image default | GPT-image-2 relay as image primary | 2026-05-28 review | image_gen active_id changed to gpt_image2_relay |
| EasyMedia/Yimei for publishing | Douyin API + Playwright for each platform | 2026-05-28 review | No public API for EasyMedia; dual-track approach confirmed |

**Deprecated/outdated:**
- **MiniMax as default production model:** The 2026-05-28 review downgraded all MiniMax models to baseline/兜底 only. Do not set MiniMax as active_id for any function slot.
- **EasyMedia/Yimei for publishing:** Confirmed no public API. Use platform-specific APIs + Playwright.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | MiMo VoiceClone API endpoint is `{base_url}/v1/audio/speech` with model `mimo-v2.5-tts-voiceclone` | Voice Service | MiMo platform may have different API; requires fallback to external TTS |
| A2 | GPT-image-2 works via New API relay using `POST /v1/responses` with `openai_responses` compatibility | Image Generation | Relay may not support responses API; requires fallback to direct OpenAI or alt model |
| A3 | WeChat Channels and Xiaohongshu can be automated via Playwright (login + file upload) | Publisher | Platforms may have anti-bot detection that blocks automated publishing |
| A4 | Douyin open platform API is accessible for personal developer accounts | Publisher | May require资质审核 or have limited permissions for non-enterprise accounts |
| A5 | `elevenlabs` Python SDK package is stable and installable via pip | Voice Service | Package API may differ; fallback to raw httpx always available |
| A6 | The `model_call_logs` table from Phase 2 schema has all fields needed | Model Logging | Additional fields may be needed for specific service calls; schema is extensible |
| A7 | Playwright browser can be launched headless on this Linux server without display | Publisher | May need `xvfb-run` or `--headless=new` flag for environments without X display |
| A8 | All video gen APIs have 9:16 aspect ratio support | Video Gen | Some providers may not support 9:16; must verify in eval |

## Open Questions

1. **Does the New API relay actually support GPT-image-2 via the responses API?**
   - What we know: GPT-image-2 uses `POST /v1/responses` with model `gpt-image-2`. The relay must support the OpenAI Responses API, not just Chat Completions.
   - What's unclear: Whether the configured relay supports this.
   - Recommendation: Implement a test endpoint in the image service that probes the relay. If it fails, log the error and fall back to alternative image models (Firefly, Seedream, etc.) or require a direct OpenAI API key.

2. **How should Playwright cookies be managed for long-term automated publishing?**
   - What we know: Playwright can save and restore cookies via `page.context.cookies()` and `context.add_cookies()`.
   - What's unclear: Cookie storage format (JSON), session expiry detection, and re-authentication flow.
   - Recommendation: Store cookies as JSON files per platform. Implement a `validate_login()` method that navigates to the platform and checks for login indicators. If expired, raise a notification for manual re-login.

3. **What is the exact MiMo VoiceClone API contract?**
   - What we know: The tech spec assumes `POST /v1/audio/speech` with JSON body including `model`, `text`, `voice_id`, `format`.
   - What's unclear: Whether MiMo VoiceClone requires a different endpoint or parameters than regular TTS. The platform docs are not publicly accessible.
   - Recommendation: Make the MiMo provider function flexible: define the endpoint path as a model-level override in `model_state.json`, defaulting to the assumed path. First implementation should log the exact request/response for debugging.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All services | Yes | 3.12.3 | -- |
| FFmpeg | composer.py, mock modes | Yes | 6.1.1 | -- |
| httpx | All API calls | In venv | 0.28.1 | -- |
| openai | GPT-image-2 relay | In venv | 2.38.0 | -- |
| playwright | Publisher (browser) | In venv | 1.60.0 | -- |
| tenacity | Retry/polling | In venv | 9.1.4 | -- |
| aiosqlite | model_call_logs | In venv | 0.22.1 | -- |
| Playwright browsers | Automated publishing | TBD | -- | `playwright install chromium` needed |
| MiMo API key | Voice service | From .env | -- | Mock voice if missing |
| GPT-image-2 via relay | Image generation | From .env | -- | Mock image if missing |
| Douyin/Kuaishou API keys | Publisher API | From .env | -- | Manual publish + Playwright |

**Missing dependencies with no fallback:** None — all modes have mock fallbacks.

**Missing dependencies with fallback:**
- Playwright browsers: need `playwright install chromium` before publishing. Without it, Playwright mode fails. All other modes work.
- Media API keys: all missing keys degrade gracefully to mock/local/manual modes.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest -x -q` |
| Full suite command | `pytest -v --tb=short` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SVC-02 | voice.generate returns wav file path | unit | `pytest tests/test_services/test_voice.py::test_generate_voice_returns_path -x` | Wave 0 |
| SVC-02 | voice generates mock wav when no API key | unit | `pytest tests/test_services/test_voice.py::test_voice_mock_mode -x` | Wave 0 |
| SVC-02 | voice dispatches correct provider by model_id | unit | `pytest tests/test_services/test_voice.py::test_voice_provider_dispatch -x` | Wave 0 |
| SVC-03 | digital_human.mock produces mp4 with audio | integration | `pytest tests/test_services/test_digital_human.py::test_mock_mode -x` | Wave 0 |
| SVC-03 | digital_human supports all modes | unit | `pytest tests/test_services/test_digital_human.py::test_all_modes_registered -x` | Wave 0 |
| SVC-04 | video_gen.mock produces mp4 | integration | `pytest tests/test_services/test_video_gen.py::test_mock_mode -x` | Wave 0 |
| SVC-04 | video_gen supports all provider modes | unit | `pytest tests/test_services/test_video_gen.py::test_provider_registry -x` | Wave 0 |
| SVC-05 | image_gen generates image via relay | unit | `pytest tests/test_services/test_image_gen.py::test_generate_image -x` | Wave 0 |
| SVC-05 | image_gen mock mode | unit | `pytest tests/test_services/test_image_gen.py::test_mock_mode -x` | Wave 0 |
| SVC-07 | publisher dispatches to correct platform handler | unit | `pytest tests/test_services/test_publisher.py::test_platform_dispatch -x` | Wave 0 |
| SVC-07 | publisher playright flow creates browser | unit | `pytest tests/test_services/test_publisher.py::test_playwright_setup -x` | Wave 0 |
| DATA-06 | dialect_dict.json exists with valid format | unit | `pytest tests/test_data.py::test_dialect_dict_exists -x` | Wave 0 |
| DATA-07 | knowledge_base.md exists with valid format | unit | `pytest tests/test_data.py::test_knowledge_base_exists -x` | Wave 0 |
| CHECK-07 | model_call_logs written on voice call | integration | `pytest tests/test_services/test_voice.py::test_model_call_logged -x` | Wave 0 |
| CHECK-07 | model_call_logs written on failed call | integration | `pytest tests/test_services/test_voice.py::test_failed_call_logged -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest -x -q tests/test_services/test_voice.py tests/test_services/test_digital_human.py`
- **Per wave merge:** `pytest -v --tb=short tests/`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_services/test_voice.py` — SVC-02 voice service tests
- [ ] `tests/test_services/test_digital_human.py` — SVC-03 digital human tests
- [ ] `tests/test_services/test_video_gen.py` — SVC-04 video generation tests
- [ ] `tests/test_services/test_image_gen.py` — SVC-05 image generation tests
- [ ] `tests/test_services/test_publisher.py` — SVC-07 publisher tests
- [ ] `tests/test_data.py` — DATA-06, DATA-07 data format tests
- [ ] `tests/test_services/conftest.py` — shared fixtures (mock ModelRegistry, temp output dirs, mock httpx responses)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | partial | API keys from .env / ModelRegistry; never hardcoded |
| V5 Input Validation | yes | Text input sanitized before TTS; script content validated before publish |
| V6 Cryptography | partial | ModelRegistry encrypts API keys at rest (Fernet); keys sent via HTTPS headers |

### Known Threat Patterns for Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| API key leakage in error messages | Information Disclosure | Log errors server-side only; never include raw API keys in log output |
| Unauthorized publish (automated) | Spoofing | MVP requires human confirmation before publish (pending_review -> approved gate) |
| Cookie/session hijack for automated publish | Tampering | Playwright cookies stored locally; consider encrypting at rest |
| Deepfake/AI-generated content misrepresentation | Spoofing | Compliance gate ensures AI-generated content is labeled; voice authorization records required |
| Third-party API data leakage | Information Disclosure | Account credentials, cookies, API keys never passed to generation models [CITED: tech spec data_policy] |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: venv install] — httpx 0.28.1, openai 2.38.0, playwright 1.60.0, tenacity 9.1.4, aiosqlite 0.22.1
- [VERIFIED: system install] — Python 3.12.3, FFmpeg 6.1.1
- [CITED: tech spec document] — 2026-05-28-youxian-tech-spec.md sections IV.2-IV.7: voice.py, digital_human.py, video_gen.py, image_gen.py, publisher.py, composer.py, model_call_logs schema, mock modes
- [CITED: optimization document] — 2026-05-28-model-agent-tool-optimization.md sections 2.2, 2.4, 2.5, 2.6: voice model priority, video model rankings, digital human rankings, New API relay strategy
- [CITED: Context7 docs - HeyGen API] — /websites/heygen: video generation v2 endpoint, status polling, avatar config
- [CITED: Context7 docs - ElevenLabs Python SDK] — /elevenlabs/elevenlabs-python: AsyncElevenLabs, text_to_speech.convert
- [VERIFIED: existing code] — services/composer.py (compose_video, compose_mock_video), config/model_registry.py (voice_clone, digital_human, video_gen, image_gen slots), config/settings.py (all API keys), web/database.py (get_async_db, get_db_connection)

### Secondary (MEDIUM confidence)
- [VERIFIED: npx playwright --version] — Playwright CLI 1.60.0; browsers need `playwright install chromium`
- [CITED: Context7 docs - ElevenLabs TTS API] — POST /v1/text-to-speech/{voice_id} endpoint details

### Tertiary (LOW confidence)
- [ASSUMED] — MiMo VoiceClone API endpoint path and parameters
- [ASSUMED] — GPT-image-2 works via New API relay responses API
- [ASSUMED] — Playwright can automate WeChat Channels and Xiaohongshu publishing
- [ASSUMED] — Douyin open platform API accessible for personal developer accounts

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified via venv install; pip versions documented
- Architecture: HIGH — patterns directly from reviewed tech spec; existing code confirms pattern
- Writer modes: HIGH — mock/local/manual patterns well-defined by tech spec
- Pitfalls: MEDIUM — MiMo API uncertainty, Playwright ant-bot detection risks are real but unverified
- Publisher API details: MEDIUM — Douyin/Kuaishou API specifics partially unverified; fallback architecture well-designed

**Research date:** 2026-05-28
**Valid until:** 2026-07-28 (stable stack); publisher API specifics may change with platform updates
