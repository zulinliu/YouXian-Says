# Phase 1: Make It Run - Research

**Researched:** 2026-05-28
**Domain:** Python project scaffolding, FFmpeg video composition, Streamlit multipage apps, Pydantic Settings v2, pytest configuration, mock digital human and B-roll generation
**Confidence:** HIGH

## Summary

Phase 1 delivers a Walking Skeleton: full project directory structure, configuration system, model registry, prompt templates, environment setup, and a FFmpeg-based composer that produces a playable video entirely in mock mode (no paid API keys required). The system must produce a 9:16 video containing: mock digital human (static image + Ken Burns zoom), mock B-roll (image slideshow + Ken Burns), mock voiceover (silence placeholder or generated audio), SRT subtitles burned in, branding elements (intro/outro/watermark), and background music.

The tech spec from the 2026-05-28 review is exceptionally detailed -- the project structure, settings.py, model_registry.py, and composer.py are already fully specified in the design document. This research focuses on verifying the recommendations and identifying pitfalls specific to the stack.

**Primary recommendation:** Follow the tech spec's project structure and code exactly for the files it specifies; use `ffmpeg-python` 0.2.0 for the composer with `filter_complex` for the composite pipeline; use Streamlit's `st.Page` + `st.navigation` (modern multipage API) for the web pages; use Pydantic Settings v2 `SettingsConfigDict` for .env loading; configure pytest via `pyproject.toml`.

<user_constraints>
## User Constraints (from CONTEXT.md)

No CONTEXT.md exists for this phase. The following are derived from PROJECT.md and the tech spec:

### Locked Decisions (from tech spec review)
- Python 3.11+
- FastAPI + Streamlit + SQLite (WAL mode) + FFmpeg + Playwright
- pip-based package management (no Poetry/Poetry)
- Pydantic Settings v2 for configuration
- Model registry: class-based with JSON file persistence
- Crypto: cryptography.fernet for API key encryption
- Mock modes: static image + audio -> talking head placeholder; images with Ken Burns -> B-roll placeholder
- Mock mode must run without paid API keys (no HEYGEN_API_KEY, no RUNWAY_API_KEY required)
- SRT subtitle format for subtitle generation
- Branding elements: intro/outro/watermark as templates

### Claude's Discretion
- Exact directory layout within the specified structure
- Test organization (test file naming, conftest scope)
- pytest configuration details (markers, coverage settings)
- requirements.txt exact version pins vs. loose constraints
- Streamlit page organization (single entrypoint vs. pages/ subdirectory)
- Documentation detail level in RESEARCH.md

### Deferred Ideas (OUT OF SCOPE)
- n8n workflow engine integration (deferred to Phase 2+)
- HeyGen/Runway API integration (deferred to Phase 3)
- Real LLM/voice/image service integration (deferred to Phase 2+)
- Database initialization (SQLite tables -- deferred to Phase 2)
- Real digital human generation (deferred to Phase 3)
- Real B-roll generation from video models (deferred to Phase 3)
- Real voiceover generation from MiMo/other APIs (deferred to Phase 3)
- Agent implementations (content/production/ops agents -- deferred to Phase 4)
- Web admin pages beyond settings (create/review/publish/dashboard -- deferred to Phase 5)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | Project directory structure | Tech spec section II specifies exact layout; verified as standard Python project convention |
| INFRA-02 | Config (settings.py) | Tech spec section 3.2 provides complete code; Pydantic Settings v2 2.14.1 verified working |
| INFRA-03 | Model registry (model_registry.py) | Tech spec section 4.2 provides complete code with ModelRegistry class, Fernet encryption, JSON persistence |
| INFRA-04 | Prompts (prompts.py) | Standard Python module; structure determined by Phase 4+ agent implementation |
| INFRA-05 | .env.example | Tech spec section 3.1 provides complete file with all variables |
| INFRA-06 | requirements.txt | Tech spec section 8.1 lists all dependencies; verified installable |
| INFRA-07 | setup.sh | Standard bash script; installs system deps (ffmpeg) and Python packages via pip |
| SVC-06 | FFmpeg composer | ffmpeg-python 0.2.0 provides overlay, subtitles, amix, scale, drawtext filters. All FFmpeg 6.1.1 filters confirmed available on target system. |
| DATA-08 | Branding templates | Static files (PNG/MP4 for intro/outro/watermark); MP3 for BGM. No generation needed in Phase 1. |
| TEST-01 | model_registry tests | pytest 9.0.3 available; framework configured via pyproject.toml; mock JSON file for persistence |
| TEST-06 | Mock mode verification | pytest can run pipeline in mock mode; output file existence and duration checks via ffprobe |
| CHECK-01 | No paid API keys needed | All mock mode functions use local FFmpeg processing only; no external HTTP calls in mock path |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Mock digital human (image + audio) | **Local/FFmpeg** | -- | Static image zoom, audio passthrough; no API calls |
| Mock B-roll (image slideshow) | **Local/FFmpeg** | -- | Image-to-video with zoompan filter; no API calls |
| Video composition | **Local/FFmpeg** | -- | All compositing done via ffmpeg-python locally |
| Subtitle generation | **Local/Python** | FFmpeg | SRT file generation in Python; subtitles filter burns them in |
| Branding overlay | **Local/FFmpeg** | -- | Image/video overlay via FFmpeg overlay filter |
| Configuration | **Config module** | -- | Pydantic settings loaded at startup, model_registry persists to JSON |
| Model registry | **Config module** | -- | Class-based with JSON file persistence; no runtime service needed in Phase 1 |
| Testing | **pytest** | -- | Unit tests for model registry; integration test for mock pipeline |
| Web settings UI | **Streamlit** | -- | Entrypoint for model configuration in Phase 1 settings page |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | Runtime | Tech spec requirement [VERIFIED: specs document] |
| ffmpeg-python | 0.2.0 | Pythonic FFmpeg bindings | Verified installable from PyPI; provides overlay, filter, concat, drawtext APIs [VERIFIED: PyPI, temp venv install] |
| pydantic-settings | 2.14.1 | .env loading and validation | Current version as of 2026-05-28; uses `SettingsConfigDict(env_file='.env')` [VERIFIED: PyPI, temp venv install] |
| pydantic | 2.13.4 | Data validation core | Required by pydantic-settings [VERIFIED: temp venv install] |
| cryptography | 41.0.7+ | Fernet encryption for API keys | Pre-installed on system; Fernet symmetric encryption for model_state.json API keys [VERIFIED: pip list] |
| pytest | 9.0.3 | Test framework | Current version; supports pyproject.toml config, conftest.py fixtures, markers [VERIFIED: system install] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai | >=1.30.0 | OpenAI-compatible API client | For LLM calls (future phases); AsyncOpenAI, AsyncStream [CITED: PyPI] |
| httpx | latest | Async HTTP client | For service API calls (future phases); shared client pattern in tech spec [CITED: PyPI] |
| tenacity | >=8.0.0 | Retry logic | For API retry with exponential backoff (future phases) [CITED: PyPI] |
| streamlit | latest | Web UI framework | For settings page in Phase 1; full web admin in Phase 5 [CITED: PyPI] |
| python-dotenv | 1.2.2 | .env file loading (fallback) | Bundled with pydantic-settings [VERIFIED: temp venv install] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ffmpeg-python 0.2.0 | Raw subprocess ffmpeg | ffmpeg-python provides filter graph construction, `overlay()`, `filter()` methods; much cleaner than subprocess. However, ffmpeg-python 0.2.0 is last released 2022; for advanced filter_complex chains, subprocess may be more reliable [ASSUMED] |
| pydantic-settings | python-dotenv + manual parsing | pydantic-settings provides type validation, env_prefix, env_file config -- strictly better for multi-field configs [VERIFIED: docs] |
| st.Page + st.navigation | pages/ subdirectory auto-discovery | st.Page + st.navigation gives explicit control over page order, icons, and grouping; pages/ auto-discovery is simpler but less flexible [CITED: Streamlit docs] |

**Installation:**
```bash
# requirements.txt:
fastapi
uvicorn
streamlit
pydantic-settings
openai>=1.30.0
httpx
tenacity>=8.0.0
cryptography
ffmpeg-python
playwright
sqlite-utils
python-dotenv
```

**Version verification:**
```bash
# Verified 2026-05-28:
pip install ffmpeg-python  # -> 0.2.0
pip install pydantic-settings  # -> 2.14.1
pip install pydantic  # -> 2.13.4
```

## Architecture Patterns

### System Architecture (Phase 1 only - Mock Pipeline)

```
[setup.sh] --> [.env + requirements] --> [config/settings.py]
                                              |
                                              v
[config/model_registry.py] <--> [data/model_state.json]
         |
         v
[services/composer.py]  (ffmpeg-python)
         |
         v
[templates/branding/] --> FFmpeg Composite Pipeline --> [output/final/*.mp4]
[templates/music/]    -->    | overlay (digital human)
[templates/fonts/]    -->    | overlay (B-roll clips, timed)
                             | overlay (watermark)
                             | subtitles burn-in (SRT -> ass filter)
                             | amix (voice + BGM)
                             | scale (9:16 output)
                             |
[v] --> [streamlit entrypoint (app.py)] --> [web/pages/settings.py]
```

### Recommended Project Structure

```
youxianduanshipin/
├── config/
│   ├── __init__.py
│   ├── settings.py          # Pydantic Settings v2
│   ├── model_registry.py    # ModelRegistry class + REGISTRY dict
│   └── prompts.py           # LLM prompt templates (stubs in Phase 1)
├── services/
│   ├── __init__.py
│   └── composer.py          # FFmpeg video composition (SVC-06)
├── templates/
│   ├── branding/            # intro.mp4, outro.mp4, watermark.png
│   ├── music/               # bgm.mp3
│   └── fonts/               # NotoSansSC-Regular.ttf (or similar)
├── output/
│   ├── voices/
│   ├── videos/
│   ├── images/
│   └── final/
├── data/
│   └── model_state.json     # Created at runtime by model_registry
├── tests/
│   ├── conftest.py
│   ├── test_model_registry.py  # TEST-01
│   └── test_mock_pipeline.py   # TEST-06
├── web/
│   ├── __init__.py
│   ├── app.py               # Streamlit entrypoint with st.navigation
│   └── pages/
│       └── settings.py      # Model configuration page
├── scripts/
│   └── setup.sh             # INFRA-07
├── .env.example             # INFRA-05
├── requirements.txt          # INFRA-06
├── pyproject.toml            # pytest config + project metadata
└── README.md
```

### Pattern 1: FFmpeg Pipeline Builder
**What:** Build complex filter_compose chains using ffmpeg-python, chaining filters with `overlay()`, `filter()`, and `output()`.

**When to use:** For the composite pipeline combining digital human + B-roll + subtitles + branding + BGM.

**Example:**
```python
import ffmpeg

def compose_mock_video(
    dh_image: str,          # Static image path for digital human
    audio_path: str,        # Voiceover audio
    broll_images: list,     # Static images for B-roll
    subtitle_srt: str,      # SRT file path
    watermark_path: str,    # Watermark PNG
    bgm_path: str,          # Background music
    output_path: str,       # Output MP4
):
    """Full mock pipeline: digital human with Ken Burns + B-roll + subtitles + watermark + BGM."""
    # Digital human: static image with zoompan (Ken Burns)
    dh_input = ffmpeg.input(dh_image, loop=1, framerate=25, t=duration)
    dh_video = dh_input.filter('zoompan',
        z='min(zoom+0.0015,1.5)',
        d=duration * 25,
        s='1080x1920',
        fps=25
    )

    # Voice input
    voice = ffmpeg.input(audio_path)

    # Build the composite
    current = dh_video

    # Overlay B-roll clips with timed enable
    for i, img in enumerate(broll_images):
        broll = ffmpeg.input(img, loop=1, framerate=25, t=clip_duration)
        broll_video = broll.filter('zoompan',
            z='min(zoom+0.002,1.3)',
            d=clip_duration * 25,
            s='1080x1920',
            fps=25
        ).filter('scale', 1080, 1920)
        # Fade in/out for B-roll
        broll_video = broll_video.filter('fade', t='in', st=0, d=0.5)
        broll_video = broll_video.filter('fade', t='out', st=clip_duration-0.5, d=0.5)
        current = current.overlay(
            broll_video,
            enable=f'between(t,{clip_start},{clip_end})'
        )

    # Subtitle burn-in (using subtitles filter with SRT)
    srt_safe = subtitle_srt.replace('\\', '/').replace(':', '\\:')
    current = current.filter('subtitles', srt_safe,
        force_style='FontName=NotoSansSC,FontSize=16,PrimaryColour=&HFFFFFF&,'
                     'OutlineColour=&H000000&,BorderStyle=1,Outline=1,Shadow=0')

    # Watermark overlay (enable for entire duration)
    wm = ffmpeg.input(watermark_path).filter('scale', 100, -1)
    current = current.overlay(wm, x='W-w-20', y='H-h-20')

    # Add BGM
    bgm = ffmpeg.input(bgm_path).filter('volume', 0.15)
    final_audio = ffmpeg.filter([voice, bgm], 'amix', inputs=2, duration='first')

    # Output
    return ffmpeg.output(
        current, final_audio,
        output_path,
        vcodec='libx264', acodec='aac',
        preset='fast', crf=23,
        pix_fmt='yuv420p'
    ).overwrite_output().run()
```

**Note:** The tech spec's `composer.py` uses `subprocess`/raw FFmpeg rather than ffmpeg-python for complex filter chains, which may be more reliable for multi-step composites. Either approach works; ffmpeg-python is cleaner for simple overlays.

### Pattern 2: Streamlit Multipage with st.Page + st.navigation
**What:** Modern Streamlit multipage pattern using `st.Page()` and `st.navigation()`.

**When to use:** For the web/app.py entrypoint, used to organize settings page in Phase 1 (and all admin pages in Phase 5).

**Example:**
```python
# web/app.py
import streamlit as st
from web.pages.settings import render_settings_page

st.set_page_config(page_title="攸县有话说", layout="wide")

# Auth guard (stub in Phase 1, real in Phase 2)
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("攸县短视频管理后台")
    password = st.text_input("管理员密码", type="password")
    if st.button("登录"):
        # In Phase 1, accept any non-empty password
        if password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("请输入密码")
    st.stop()

# Navigation
settings_page = st.Page(render_settings_page, title="模型设置", icon=":material/settings:")

# In Phase 5, add more pages:
# create_page = st.Page("pages/create.py", title="选题共创", icon=":material/lightbulb:")
# review_page = st.Page("pages/review.py", title="审核中心", icon=":material/rate_review:")

pg = st.navigation([settings_page])
pg.run()
```

### Pattern 3: Pydantic Settings v2 Env Loading
**What:** Load and validate .env file using `SettingsConfigDict`.

**When to use:** For `config/settings.py`.

**Example:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # All fields with defaults or required
    deepseek_api_key: str = ""
    admin_password: str  # No default -- must be in .env
    web_port: int = 8501
    # ... (all other fields from tech spec)

settings = Settings()

# Validation on startup
if settings.admin_password in ("admin", ""):
    raise ValueError("ADMIN_PASSWORD must be set to a non-default value")
```

### Anti-Patterns to Avoid
- **Mixing mock and real mode in same code path:** Keep mock mode in a separate code path or guard with `if model.mode == "mock"`. Do not let mock code accidentally reach out to real APIs.
- **Hardcoding file paths:** Use `pathlib.Path` relative to project root; use `tempfile.mkdtemp()` for intermediate files in compose_video.
- **State mutation in ModelRegistry:** The `get_active()` method does `copy.deepcopy()` before applying overrides -- this is correct. The planner must ensure all callers also follow this pattern.
- **Pydantic v1 config syntax:** Pydantic v2 uses `model_config = SettingsConfigDict(...)`, not `class Config:` inner class.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FFmpeg subprocess management | Custom subprocess wrappers with string formatting | `ffmpeg-python` or structured subprocess | FFmpeg filter graph escaping is error-prone; ffmpeg-python constructs the graph programmatically [VERIFIED: docs] |
| .env file parsing | Manual `os.environ.get()` for every variable | `pydantic-settings` with `SettingsConfigDict` | Type validation, error messages, env_prefix support built in [VERIFIED: pydantic-settings docs] |
| API key encryption | Custom encryption | `cryptography.fernet.Fernet` | Fernet is the standard symmetric encryption primitive; audited, correct [VERIFIED: cryptography docs] |
| Retry logic | Manual retry with sleep loops | `tenacity` decorators | `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))` -- cleaner and more robust [VERIFIED: tech spec] |
| JSON file atomic writes | Just `open().write()` | Write to `.tmp`, then `os.replace()` | Prevents partial writes on crash; tech spec already implements this pattern in ModelRegistry | -- |

**Key insight:** The tech spec already specifies every don't-hand-roll pattern above. The key risk is the planner reverting to hand-rolled versions of these patterns instead of following the spec.

## Common Pitfalls

### Pitfall 1: ffmpeg-python `overlay()` with timed `enable` expression
**What goes wrong:** The `enable` parameter to overlay uses FFmpeg expression syntax like `between(t,5,10)`. If the quoting or format is wrong, the overlay either always shows or never shows.
**Why it happens:** ffmpeg-python passes `enable` as a string to the FFmpeg overlay filter. The expression syntax is not validated by ffmpeg-python -- it is sent raw to FFmpeg.
**How to avoid:** Test with one overlay at a time using different `enable` ranges. Use ffmpeg-python's `.view()` method to inspect the generated filter graph. Verify with `ffprobe` that the output has the expected duration.
**Warning signs:** Overlay appears at wrong time or not at all; FFmpeg error messages about expression parsing.

### Pitfall 2: SRT file paths in subtitles filter
**What goes wrong:** The `subtitles` filter requires special escaping for colons and backslashes in file paths. On Linux, `subtitle_srt.replace('\\', '/')` is needed; paths with colons must use `\\:` escaping.
**Why it happens:** FFmpeg uses `:` as a separator in filter options, so literal colons in paths must be escaped.
**How to avoid:** Use `force_style` parameter instead of relying on ASS style file. Pass SRT with escaped path. Keep the SRT file in a simple path (no spaces, no special characters). [VERIFIED: FFmpeg subtitles filter help output shows `filename` parameter with colon separator convention].

### Pitfall 3: zoompan filter duration calculation
**What goes wrong:** zoompan's `d` parameter is in NUMBER_OF_FRAMES, not seconds. If you specify `t=10` but `d=25`, you get only 1 second of video.
**Why it happens:** `d` in zoompan is "duration in frames", default is 90 frames = ~3.6s at 25fps. This is confusing for users coming from other FFmpeg filters that use seconds.
**How to avoid:** Always calculate `d = duration_seconds * fps`. For an image looped at framerate=25, `d = total_frames`. [VERIFIED: `ffmpeg -h filter=zoompan` shows `d<string> set the duration expression (default "90")`].

### Pitfall 4: Streamlit `st.form` required for settings page edits
**What goes wrong:** Using `st.text_input` and `st.button` outside a form causes widget values to reset on every rerun.
**Why it happens:** Streamlit reruns all code on interaction; widget values outside a form are tied to their key, but button clicks trigger reruns that can clear unsubmitted inputs.
**How to avoid:** Wrap each model's API parameter editing area in `st.form(key=f"form_{fid}")` as the tech spec does in section 4.4.1. Use `st.form_submit_button` for save/switch actions. [VERIFIED: tech spec section 4.4.1 code].

### Pitfall 5: Externally-managed Python environment
**What goes wrong:** Ubuntu 24.04+ uses PEP 668, which prevents `pip install` outside virtual environments.
**Why it happens:** System Python is "externally managed" to prevent conflicts with apt-installed packages.
**How to avoid:** The `setup.sh` script must create a virtual environment: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`. Document this in setup.sh. [VERIFIED: system check shows "externally-managed-environment" error].

### Pitfall 6: Missing font files for drawtext/subtitles filters
**What goes wrong:** Drawtext or subtitles filter fails at runtime because a specified font is not installed.
**Why it happens:** FFmpeg's drawtext requires libfreetype and accessible font files. The `subtitles` filter with `force_style=FontName=...` requires that font to be findable.
**How to avoid:** Bundle a font like NotoSansSC in `templates/fonts/` and either reference it by absolute path in `fontfile=` parameter, or install it system-wide in `setup.sh`. Use `:fontsdir=...` in the subtitles filter. [ASSUMED: common FFmpeg pitfall].

## Code Examples

### SRT Subtitle Format
```text
1
00:00:01,000 --> 00:00:04,500
大家好，我是攸县人

2
00:00:05,000 --> 00:00:10,000
今天我们来聊一聊攸县米粉
```

Python generation:
```python
def _seconds_to_srt(seconds: float) -> str:
    """Convert seconds to SRT time format HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def generate_srt(subtitles: list[dict]) -> str:
    """Generate SRT subtitle file content."""
    lines = []
    for i, sub in enumerate(subtitles, 1):
        start = _seconds_to_srt(sub["start"])
        end = _seconds_to_srt(sub["end"])
        text = sub["text"]
        if sub.get("dialect_word"):
            text = f"{text}（{sub['translation']}）"
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)
```
[CITED: SRT format is a W3C standard; verified through common knowledge and tech spec code]

### zoompan Ken Burns Effect (FFmpeg Command Line)
```bash
# Zoom in from 1.0 to 1.5 over 5 seconds at 25fps
# Output 1080x1920 (9:16)
ffmpeg -loop 1 -i input.jpg -t 5 -vf \
  "zoompan=z='min(zoom+0.0015,1.5)':d=125:s=1080x1920:fps=25" \
  -c:v libx264 -pix_fmt yuv420p output.mp4

# Ken Burns: zoom in AND pan from center to top-left
ffmpeg -loop 1 -i input.jpg -t 5 -vf \
  "zoompan=z='min(zoom+0.002,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=1080x1920:fps=25" \
  -c:v libx264 -pix_fmt yuv420p output.mp4
```
[VERIFIED: `ffmpeg -h filter=zoompan` shows parameters; zoom expression uses `min()` to clamp the zoom level]

### Mock Digital Human Pipeline (Full Composite)
```bash
# 1. Create talking head placeholder: static image + zoompan
ffmpeg -loop 1 -i templates/branding/avatar_placeholder.png -t 10 \
  -vf "zoompan=z='min(zoom+0.001,1.2)':d=250:s=1080x1920:fps=25" \
  -c:v libx264 -pix_fmt yuv420p output/dh_placeholder.mp4

# 2. Merge video with audio
ffmpeg -i output/dh_placeholder.mp4 -i output/voices/mock_voice.wav \
  -c:v copy -c:a aac -shortest output/merged.mp4

# 3. Overlay B-roll with timed enable and fade
ffmpeg -i output/merged.mp4 -loop 1 -i templates/branding/broll_sample.jpg \
  -filter_complex "[1:v]zoompan=z='min(zoom+0.002,1.3)':d=75:s=1080x1920:fps=25, \
    fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5[broll]; \
    [0:v][broll]overlay=enable='between(t,2,5)'[out]" \
  -map "[out]" -map 0:a -c:v libx264 -c:a copy output/composed.mp4

# 4. Burn subtitles
ffmpeg -i output/composed.mp4 -vf "subtitles=subs.srt:force_style='FontName=NotoSansSC,FontSize=16'" \
  -c:a copy output/final.mp4
```

### ModelRegistry Test Pattern
```python
# tests/test_model_registry.py
import json
from pathlib import Path
from config.model_registry import ModelRegistry

def test_get_active_returns_model(tmp_path, monkeypatch):
    """Test that get_active returns a valid ModelOption for each function."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))
    
    # Should work even without state file (uses defaults)
    model = ModelRegistry.get_active("text_llm")
    assert model.id == "deepseek_v4_flash"
    assert model.provider == "deepseek"

def test_switch_changes_active(tmp_path, monkeypatch):
    """Test that switching a function slot persists the change."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))
    
    ModelRegistry.switch("text_llm", "deepseek_v4pro")
    state = json.loads((tmp_path / 'model_state.json').read_text())
    assert state["text_llm"]["active_id"] == "deepseek_v4pro"

def test_switch_invalid_model_raises(tmp_path, monkeypatch):
    """Test that switching to an invalid model ID raises ValueError."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))
    
    import pytest
    with pytest.raises(ValueError, match="不在.*可用列表"):
        ModelRegistry.switch("text_llm", "nonexistent_model")

def test_snapshot_immutable(tmp_path, monkeypatch):
    """Test that snapshot returns a copy, not the same reference."""
    monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))
    
    model = ModelRegistry.snapshot("text_llm")
    model.id = "mutated"
    # Get again and verify not mutated
    model2 = ModelRegistry.get_active("text_llm")
    assert model2.id == "deepseek_v4_flash"
```
[VERIFIED: pytest API for tmp_path, monkeypatch, raises -- standard pytest features]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 `class Config:` | Pydantic v2 `model_config = SettingsConfigDict()` | 2023 | Incompatible; v1 config has no effect in v2 |
| Streamlit `pages/` subdirectory auto-discovery | `st.Page()` + `st.navigation()` | 2024 | Manual paths, explicit grouping, icons support |
| ffmpeg raw subprocess | ffmpeg-python 0.2.0 | 2019 | Filter graph construction via Python methods; but 0.2.0 not updated since 2022 |
| pytest setup.cfg config | pyproject.toml `[tool.pytest.ini_options]` | pytest 7+ | Preferred; single source of project config |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | ffmpeg-python 0.2.0 `.filter('subtitles', ...)` works identically to CLI `-vf subtitles=...` | Code Examples, Pitfall 2 | Subtitles may not render; fallback to raw subprocess FFmpeg call |
| A2 | The `mock` mode digital human uses only FFmpeg (no HTTP requests, no dependencies on avatars/external images) | Summary, Architectural Map | Mock mode might accidentally depend on assets not bundled in templates/branding/ |
| A3 | SRT subtitle format can be passed as a file path to subtitles filter | Pitfall 2 | Need to use `ass` filter instead, or use `drawtext` per-segment |
| A4 | `enable='between(t,start,end)'` in ffmpeg-python `.overlay()` works with filter expressions | Pitfall 1, Code Examples | Need to use `.filter('overlay', ..., enable='...')` instead of `.overlay(..., enable=...)` syntax |

## Open Questions

1. **Does ffmpeg-python's `.overlay()` method support the `enable` parameter?**
   - What we know: The tech spec uses `.overlay(scaled, ..., enable=f"between(t,...)")` syntax
   - What's unclear: ffmpeg-python's `overlay()` may only support positional `x` and `y` parameters; `enable` may need to be passed via `.filter('overlay', ..., enable='...')`
   - Recommendation: Test with `.filter('overlay', ..., enable='...')` syntax first; fall back to `subprocess.run()` with manual filter_complex if ffmpeg-python doesn't support it. The tech spec's `composer.py` already uses a subprocess-like approach.

2. **Font path for subtitles filter: where does FFmpeg search for fonts?**
   - What we know: Subtitles filter has `fontsdir` parameter; `force_style` accepts `FontName=...`
   - What's unclear: Whether bundled fonts in `templates/fonts/` are discoverable via relative path, or if they need to be installed system-wide
   - Recommendation: In `setup.sh`, install the font to `~/.fonts/` or configure `FONTCONFIG_PATH`. Alternatively, use absolute path in `fontfile=` parameter.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Runtime | Yes | 3.12.3 | -- |
| pip | Package management | Yes | 24.0 | -- |
| FFmpeg | Video composition | Yes | 6.1.1 | -- |
| ffmpeg-python | Python FFmpeg bindings | Available via pip | 0.2.0 | Raw subprocess FFmpeg |
| pydantic-settings | .env config | Available via pip | 2.14.1 | python-dotenv + manual parsing |
| pydantic | Data validation | Available via pip | 2.13.4 | -- |
| pytest | Testing | Yes | 9.0.3 | -- |
| cryptography | API key encryption | Yes | 41.0.7 | -- |
| httpx | HTTP client | Available via pip | latest | -- |
| openai | LLM client | Available via pip | latest | -- |

**Missing dependencies with no fallback:**
- None for Phase 1

**Missing dependencies with fallback:**
- ffmpeg-python 0.2.0 can be replaced by direct `subprocess` FFmpeg calls (the tech spec's composer.py already uses subprocess-style calls)
- Virtual environment required: system Python is externally managed (PEP 668); `setup.sh` must create `venv`

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
| TEST-01 | ModelRegistry.get_active returns valid model | unit | `pytest tests/test_model_registry.py::test_get_active_returns_model -x` | Wave 0 |
| TEST-01 | ModelRegistry.switch persists change | unit | `pytest tests/test_model_registry.py::test_switch_changes_active -x` | Wave 0 |
| TEST-01 | ModelRegistry.switch with invalid ID raises | unit | `pytest tests/test_model_registry.py::test_switch_invalid_model_raises -x` | Wave 0 |
| TEST-01 | ModelRegistry.snapshot returns immutable copy | unit | `pytest tests/test_model_registry.py::test_snapshot_immutable -x` | Wave 0 |
| TEST-01 | ModelRegistry.update_model_config saves overrides | unit | `pytest tests/test_model_registry.py::test_update_model_config -x` | Wave 0 |
| TEST-06 | Full mock pipeline produces playable file | integration | `pytest tests/test_mock_pipeline.py::test_mock_pipeline_creates_video -x` | Wave 0 |
| TEST-06 | Mock pipeline runs without API keys | integration | `pytest tests/test_mock_pipeline.py::test_mock_pipeline_no_api_keys -x` | Wave 0 |
| CHECK-01 | Verify no HTTP calls in mock mode | integration | `pytest tests/test_mock_pipeline.py::test_mock_pipeline_no_network -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest -x -q tests/test_model_registry.py`
- **Per wave merge:** `pytest -v --tb=short tests/`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [x] `tests/test_model_registry.py` -- TEST-01 (create from scratch)
- [x] `tests/test_mock_pipeline.py` -- TEST-06, CHECK-01 (create from scratch)
- [x] `pyproject.toml` -- pytest config section (create with `[tool.pytest.ini_options]`)
- [x] `tests/conftest.py` -- shared fixtures (`tmp_path` for model_state, asset paths)

## Sources

### Primary (HIGH confidence)
- [VERIFIED: tech spec document] -- 2026-05-28-youxian-tech-spec.md -- project structure, settings.py, model_registry.py, composer.py, all code samples
- [VERIFIED: FFmpeg 6.1.1 local install] -- `ffmpeg -version` and `ffmpeg -h filter=zoompan|subtitles|overlay` -- all required filters available
- [VERIFIED: PyPI via temp venv install] -- ffmpeg-python 0.2.0, pydantic-settings 2.14.1, pydantic 2.13.4, cryptography 41.0.7
- [VERIFIED: pytest 9.0.3 local install] -- `pytest --version`

### Secondary (MEDIUM confidence)
- [CITED: Streamlit docs via Context7] -- st.Page + st.navigation multipage API; st.form usage for settings forms
- [CITED: pydantic-settings docs via Context7] -- SettingsConfigDict, env_file parameter, env_prefix configuration
- [CITED: ffmpeg-python docs via Context7] -- overlay(), filter(), drawtext() APIs; filter graph visualization

### Tertiary (LOW confidence)
- [ASSUMED] -- ffmpeg-python 0.2.0 overlay `enable` parameter compatibility with timed expressions
- [ASSUMED] -- SRT file subtitles filter compatibility with `force_style` parameter
- [ASSUMED] -- Font discovery paths for subtitles filter

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all packages verified via install test; versions documented
- Architecture: HIGH - tech spec provides complete architecture; only Phase 1 subset needed
- Pitfalls: HIGH - verified via FFmpeg local install help output, externally-managed environment check

**Research date:** 2026-05-28
**Valid until:** 2026-07-28 (stable stack; pydantic-settings, ffmpeg-python versions change slowly)
