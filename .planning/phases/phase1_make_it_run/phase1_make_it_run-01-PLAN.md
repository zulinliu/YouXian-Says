---
phase: 1-make_it_run
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - config/__init__.py
  - config/settings.py
  - config/model_registry.py
  - config/prompts.py
  - services/__init__.py
  - templates/branding/.gitkeep
  - templates/music/.gitkeep
  - templates/fonts/.gitkeep
  - output/voices/.gitkeep
  - output/videos/.gitkeep
  - output/images/.gitkeep
  - output/final/.gitkeep
  - data/.gitkeep
  - web/__init__.py
  - web/app.py
  - web/pages/__init__.py
  - web/pages/settings.py
  - scripts/.gitkeep
  - .env.example
  - requirements.txt
  - pyproject.toml
  - scripts/setup.sh
  - README.md
autonomous: true
requirements:
  - INFRA-01
  - INFRA-02
  - INFRA-03
  - INFRA-04
  - INFRA-05
  - INFRA-06
  - INFRA-07
  - SVC-06
  - DATA-08
  - TEST-01
  - TEST-06
  - CHECK-01

must_haves:
  truths:
    - "User can run `setup.sh` and get a working venv with all dependencies installed"
    - "User can inspect .env.example and understand what API keys to configure"
    - "User can import Settings from config.settings and get validated config from .env"
    - "User can query ModelRegistry to see active model configuration for each function slot"
    - "User can switch active model via ModelRegistry.switch() and change persists to JSON"
    - "User can launch Streamlit web app and see model settings page"
    - "Prompts.py can be imported without errors"
  artifacts:
    - path: "config/settings.py"
      provides: "Pydantic Settings v2 config loaded from .env"
      min_lines: 10
      exports: ["Settings", "settings"]
    - path: "config/model_registry.py"
      provides: "ModelOption, FunctionSlot dataclasses; REGISTRY dict; ModelRegistry class"
      min_lines: 100
      exports: ["ModelOption", "FunctionSlot", "REGISTRY", "ModelRegistry"]
    - path: "config/prompts.py"
      provides: "Prompt templates (stubs in Phase 1)"
      exports: ["DEFAULT_SYSTEM_PROMPT"]
    - path: ".env.example"
      provides: "All env vars documented with placeholder values"
    - path: "requirements.txt"
      provides: "All pip dependencies"
    - path: "pyproject.toml"
      provides: "Project metadata + pytest config"
    - path: "web/app.py"
      provides: "Streamlit entrypoint with auth guard + navigation"
    - path: "web/pages/settings.py"
      provides: "Model settings page with forms, switch, test connection"
    - path: "scripts/setup.sh"
      provides: "One-click setup: venv creation + pip install + ffmpeg check"
  key_links:
    - from: "config/settings.py"
      to: ".env"
      via: "SettingsConfigDict(env_file='.env')"
    - from: "config/model_registry.py"
      to: "data/model_state.json"
      via: "_load_state/_save_state file IO"
    - from: "web/app.py"
      to: "web/pages/settings.py"
      via: "st.Page(render_settings_page)"
    - from: "web/pages/settings.py"
      to: "config/model_registry.py"
      via: "ModelRegistry.list_all/switch/update_model_config/test_api_connection"

threat_model:
  trust_boundaries:
    - boundary: "Streamlit web app -> filesystem"
      description: "Web settings page reads/writes model_state.json and calls FFmpeg"
    - boundary: "user .env file -> settings.py"
      description: "Sensitive API keys are loaded from env"
  threats:
    - id: T-1-01
      category: "Information Disclosure"
      component: "config/model_registry.py"
      disposition: "mitigate"
      mitigation: "API keys encrypted via cryptography.fernet.Fernet before writing to model_state.json; masked on display"
    - id: T-1-02
      category: "Information Disclosure"
      component: "config/settings.py"
      disposition: "mitigate"
      mitigation: "settings instance kept in memory; not serialized; no log output of raw keys"
    - id: T-1-03
      category: "Elevation of Privilege"
      component: "web/app.py"
      disposition: "mitigate"
      mitigation: "Auth guard checks admin_password before rendering pages; Streamlit bound to 127.0.0.1"
    - id: T-1-04
      category: "Tampering"
      component: "data/model_state.json"
      disposition: "accept"
      mitigation: "Local single-user setup; JSON file on local filesystem behind auth gate"
</threat_model>

<verification>
- [ ] `bash scripts/setup.sh` exits 0 and venv created
- [ ] `source venv/bin/activate && python -c "from config.settings import settings; print(settings.web_port)"` prints "8501"
- [ ] `source venv/bin/activate && python -c "from config.model_registry import ModelRegistry; m = ModelRegistry.get_active('text_llm'); print(m.id)"` prints "deepseek_v4_flash"
- [ ] `pytest -x -q tests/test_model_registry.py` passes (tests created in Plan 04)
- [ ] `source venv/bin/activate && streamlit run web/app.py --server.port 8501 --server.address 127.0.0.1 &` starts without import errors
</verification>

<success_criteria>
1. Project directory structure matches tech spec section II exactly
2. config/settings.py loads all .env variables with Pydantic Settings v2
3. config/model_registry.py contains all 7 function slots with 38+ ModelOption definitions matching tech spec section 4.2
4. ModelRegistry supports get_active/snapshot/switch/update_model_config/list_all/get_model_config
5. API keys encrypted with Fernet, masked on web display
6. .env.example contains all documented variables
7. requirements.txt installable via pip in a fresh venv
8. pyproject.toml configures pytest
9. Streamlit app starts without import errors (settings page with forms)
10. README.md documents setup steps
</success_criteria>

<output>
After completion, create `.planning/phases/phase1_make_it_run/01-01-SUMMARY.md`
</output>

---

## Phase Overview

**Phase 1: Make It Run** - 搭建完整项目目录结构，通过全 Mock 模式跑通从配置到视频合成的完整管道，产出第一条可审核的攸县方言短视频。

**Mode**: MVP (Vertical Walking Skeleton)

### Requirements Map

| Req ID | Description | Plan | Status |
|--------|-------------|------|--------|
| INFRA-01 | Project directory structure | Plan 01 | Wave 1 |
| INFRA-02 | Config (settings.py) | Plan 01 | Wave 1 |
| INFRA-03 | Model registry (model_registry.py) | Plan 01 | Wave 1 |
| INFRA-04 | Prompts (prompts.py) | Plan 01 | Wave 1 |
| INFRA-05 | .env.example | Plan 01 | Wave 1 |
| INFRA-06 | requirements.txt | Plan 01 | Wave 1 |
| INFRA-07 | setup.sh | Plan 01 | Wave 1 |
| SVC-06 | FFmpeg composer (mock mode) | Plan 02 | Wave 1 |
| DATA-08 | Branding templates | Plan 02 | Wave 1 |
| TEST-01 | model_registry tests | Plan 04 | Wave 2 |
| TEST-06 | Mock pipeline test | Plan 04 | Wave 2 |
| CHECK-01 | No paid API keys in mock mode | Plan 04 | Wave 2 |

### Wave Structure

| Wave | Plans | Description |
|------|-------|-------------|
| 1 | Plan 01, Plan 02 | Project skeleton + Config + Composer (parallel - no file overlap) |
| 2 | Plan 04 | Tests (depends on Plan 01 + Plan 02) |

---

## Plan 01: Project Skeleton & Config (Wave 1)

**Objective**: Create complete project directory structure, configuration system, model registry, prompt stubs, environment setup files, and Streamlit settings page.

**Purpose**: Establish the Walking Skeleton foundation -- all infrastructure files that everything else depends on.

**Output**: Working project directory with importable config modules, installable dependencies, and a Streamlit settings page.

### Task 1.1: Create directory structure and config modules

<task type="auto">
  <name>Create project directory structure and core config modules</name>
  <files>
    config/__init__.py
    config/settings.py
    config/model_registry.py
    config/prompts.py
    services/__init__.py
    templates/branding/.gitkeep
    templates/music/.gitkeep
    templates/fonts/.gitkeep
    output/voices/.gitkeep
    output/videos/.gitkeep
    output/images/.gitkeep
    output/final/.gitkeep
    data/.gitkeep
    web/__init__.py
    web/pages/__init__.py
    scripts/.gitkeep
  </files>
  <action>
    Create the full project directory tree under `` matching tech spec section II. Directories: config/, services/, templates/branding/, templates/music/, templates/fonts/, agents/, output/voices/, output/videos/, output/images/, output/final/, data/, tests/, web/, web/pages/, scripts/.

    Key implementation details per tech spec:

    1. `config/__init__.py` - empty

    2. `config/settings.py` - Pydantic Settings v2 (NOT v1). Use `from pydantic_settings import BaseSettings, SettingsConfigDict`. Define:
       - All fields from tech spec section 3.2: deepseek_api_key, minimax_api_key, minimax_group_id, mimo_api_key, mimo_base_url, openai_relay_api_key, openai_relay_base_url, anthropic_relay_api_key, anthropic_relay_base_url, glm_relay_api_key, glm_relay_base_url, openai_api_key, anthropic_api_key, firefly_api_key, seedream_api_key, flux_api_key, heygen_api_key, heygen_avatar_id, heygen_plan, kling_access_key, kling_secret_key, runway_api_key, google_cloud_project, luma_api_key, pika_api_key, elevenlabs_api_key, cartesia_api_key, openai_tts_api_key, tavus_api_key, d_id_api_key, akool_api_key, admin_password, web_port, n8n_webhook_url, search_api_key, object_storage_endpoint, object_storage_bucket, object_storage_access_key, object_storage_secret_key, deepseek_base_url (default "https://api.deepseek.com"), mimo_api_key, mimo_base_url
       - Use `model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')`
       - Add admin_password validation: `if settings.admin_password in ("admin", ""): raise ValueError(...)`
       - Create singleton `settings = Settings()` at module level
       - CRITICAL: Do NOT use Pydantic v1 `class Config:` inner class syntax -- v2 uses `model_config`

    3. `config/model_registry.py` - Complete implementation from tech spec section 4.2:
       - ModelOption dataclass with all fields: id, name, provider, api_base, model_name, api_key_env, cost_per_m_tokens, max_context, channel, modalities, quality_tier, cost_tier, latency_tier, data_policy, api_compatibility, supports_json, supports_tools, supports_image_edit, supports_reference_image, supports_9_16, fallback_ids, notes, resolved_api_key
       - FunctionSlot dataclass: function_id, function_name, options, active_id
       - REGISTRY dict with all 7 function slots: text_llm, multimodal, image_gen, video_gen, voice_clone, digital_human
       - Each slot must contain all ModelOption entries matching tech spec (38+ total models)
       - ModelRegistry class with methods: get_active(), snapshot(), switch(), update_model_config(), get_model_config(), list_all(), _load_state(), _save_state()
       - Cryptography: Fernet encryption/decryption functions (_get_cipher, _encrypt, _decrypt, _mask)
       - Atomic write pattern: write to .tmp then os.replace(), backup old file to .bak
       - Deep copy in get_active() to avoid mutating REGISTRY global
       - API Key priority: overrides > env var
       - IMPORTANT: The model_state.json path must NOT be hardcoded to an absolute path. Use a relative path `data/model_state.json` that resolves from the project root. This file is created at runtime, not during setup.

    4. `config/prompts.py` - Stub module:
       ```python
       """提示词模板集合"""

       DEFAULT_SYSTEM_PROMPT = "你是攸县方言短视频创作助手。用攸县方言讲攸县的风俗、美食、景点和老故事。"

       def get_prompt(name: str) -> str:
           """获取指定名称的提示词模板"""
           prompts = {
               "default": DEFAULT_SYSTEM_PROMPT,
           }
           return prompts.get(name, DEFAULT_SYSTEM_PROMPT)
       ```

    5. All `__init__.py` files: empty files
    6. All `.gitkeep` files: empty files

    CRITICAL - Do NOT create `agent/` or `agents/` directory. The tech spec section II shows `agents/` but that is for Phase 4+.
  </action>
  <verify>
    <automated>
      python3 -c "
from config.settings import Settings
from config.model_registry import ModelRegistry
from config.prompts import get_prompt
m = ModelRegistry.get_active('text_llm')
assert m.id == 'deepseek_v4_flash'
assert len(m.name) > 0
assert m.resolved_api_key == ''  # no env var set yet
print('OK: all imports working, model_registry returns default')
"
    </automated>
  </verify>
  <done>
    All config modules importable; ModelRegistry returns correct defaults; all directories exist with correct structure
  </done>
</task>

### Task 1.2: Create env config, requirements, setup script, and project metadata

<task type="auto">
  <name>Create .env.example, requirements.txt, pyproject.toml, setup.sh, README.md</name>
  <files>
    .env.example
    requirements.txt
    pyproject.toml
    scripts/setup.sh
    README.md
  </files>
  <action>
    Create project root config files:

    1. `.env.example`:
       - All env vars from tech spec section 3.1
       - Grouped by service with comments
       - Placeholder values like `sk-xxx` or empty strings
       - Include every key from settings.py: DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, MINIMAX_API_KEY, MINIMAX_GROUP_ID, MIMO_API_KEY, MIMO_BASE_URL, OPENAI_RELAY_API_KEY, OPENAI_RELAY_BASE_URL, ANTHROPIC_RELAY_API_KEY, ANTHROPIC_RELAY_BASE_URL, GLM_RELAY_API_KEY, GLM_RELAY_BASE_URL, OPENAI_API_KEY, ANTHROPIC_API_KEY, FIREFLY_API_KEY, SEEDREAM_API_KEY, FLUX_API_KEY, HEYGEN_API_KEY, HEYGEN_AVATAR_ID, HEYGEN_PLAN, KLING_ACCESS_KEY, KLING_SECRET_KEY, RUNWAY_API_KEY, GOOGLE_CLOUD_PROJECT, LUMA_API_KEY, PIKA_API_KEY, ELEVENLABS_API_KEY, CARTESIA_API_KEY, OPENAI_TTS_API_KEY, TAVUS_API_KEY, D_ID_API_KEY, AKOOL_API_KEY, YIMEI_USERNAME, YIMEI_PASSWORD, CHANMAMA_TOKEN, SEARCH_API_KEY, OBJECT_STORAGE_ENDPOINT, OBJECT_STORAGE_BUCKET, OBJECT_STORAGE_ACCESS_KEY, OBJECT_STORAGE_SECRET_KEY, ADMIN_PASSWORD, WEB_PORT, N8N_WEBHOOK_URL, MASTER_ENCRYPTION_KEY
       - Include MASTER_ENCRYPTION_KEY for Fernet key derivation

    2. `requirements.txt`:
       ```
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
       pytest
       pytest-cov
       ```

    3. `pyproject.toml`:
       ```toml
       [build-system]
       requires = ["setuptools>=68.0"]
       build-backend = "setuptools.backends._legacy:_Backend"

       [project]
       name = "youxian-says"
       version = "0.1.0"
       description = "攸县方言短视频生产系统"
       requires-python = ">=3.11"

       [tool.pytest.ini_options]
       testpaths = ["tests"]
       python_files = ["test_*.py"]
       # Do NOT add addopts = "-v" here - allow executors to choose verbosity

       [tool.coverage.run]
       source = ["config", "services"]
       ```

    4. `scripts/setup.sh`:
       ```bash
       #!/usr/bin/env bash
       set -euo pipefail

       SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
       PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

       echo "=== 攸县方言短视频系统 - 一键安装 ==="

       # Check Python version
       PYTHON="python3"
       if ! command -v $PYTHON &>/dev/null; then
           echo "ERROR: Python3 not found"
           exit 1
       fi

       # Check FFmpeg
       if ! command -v ffmpeg &>/dev/null; then
           echo "WARNING: ffmpeg not found. Install with: sudo apt install ffmpeg"
       else
           echo "OK: ffmpeg found ($(ffmpeg -version | head -1))"
       fi
       ```
       The script must:
       - cd to project root
       - Create virtual env: `python3 -m venv venv`
       - Activate and pip install -r requirements.txt
       - Copy .env.example to .env if not exists: `cp -n .env.example .env`
       - Print success instructions (edit .env, then run streamlit)
       - Handle PEP 668 (externally-managed-environment) via venv creation
       - Use `set -euo pipefail` for safety

    5. `README.md`:
       - Project title: "攸县有话说 - 攸县方言短视频生产系统"
       - Brief description
       - Quick start: `bash scripts/setup.sh`
       - Then `cp .env.example .env`, edit credentials, `streamlit run web/app.py`
       - Architecture overview (reference tech spec)
       - Phase 1 scope: mock pipeline
  </action>
  <verify>
    <automated>
      bash scripts/setup.sh 2>&1 | head -20
    </automated>
  </verify>
  <done>
    Setup.sh runs without errors; requirements.txt contains all deps; pyproject.toml has pytest config
  </done>
</task>

### Task 1.3: Implement Streamlit settings page with model registry UI

<task type="auto">
  <name>Implement Streamlit entrypoint and model settings page</name>
  <files>
    web/app.py
    web/pages/settings.py
  </files>
  <action>
    Implement the Streamlit web app with auth guard and model settings page, following tech spec sections 4.4 and 4.4.1.

    1. `web/app.py` - Streamlit entrypoint:
       - `st.set_page_config(page_title="攸县有话说", layout="wide", page_icon="🎬")`
       - Auth guard: check `st.session_state.authenticated`, show password input, validate against `settings.admin_password`
       - Navigation: `st.Page(render_settings_page, title="模型设置", icon=":material/settings:")`
       - `pg = st.navigation([settings_page]); pg.run()`
       - Use `from config.settings import settings` for auth
       - Phase 1: accept any non-empty password as simple auth; in Phase 2 this becomes real auth
       - Use `type="password"` for password input
       - `st.stop()` after auth check to prevent rendering before login
       - IMPORTANT: Import render_settings_page from web.pages.settings to avoid circular import

    2. `web/pages/settings.py` - Model settings page:
       - `def render_settings_page():` entry point
       - Call `ModelRegistry.list_all()` to get all function slots with their models
       - For each function slot, render an expander section with:
         - Slot title and description
         - Active model badge (green "当前使用" indicator)
         - For each model option in the slot:
           - Model name, provider, quality tier, notes
           - `st.form(f"form_{fid}_{mid}")` with:
             - `st.text_input("API 地址", value=...)`
             - `st.text_input("模型名称", value=...)`
             - `st.text_input("API Key", type="password", placeholder=...)`
             - Two columns with form_submit_button: "保存参数" and "切换到该模型"
           - "测试连��" button outside form (separate section)
       - Use `st.toast()` for feedback (NOT rerun) -- per tech spec 4.4.1 optimization
       - `test_api_connection()` helper function: call the model's API base to verify connectivity
         - In Phase 1, this is a stub that checks if URL is reachable (no real API call needed)
       - Import ModelRegistry from config.model_registry

    IMPORTANT: The test_api_connection function in Phase 1 must NOT make real API calls (per CHECK-01). Instead:
    - Check that the URL starts with https://
    - Check that required env vars are set for the provider
    - Return result: `{"ok": True/False, "latency_ms": 0, "error": "..."}`
    - This will be made real in Phase 3 when real services are implemented
  </action>
  <verify>
    <automated>
      source venv/bin/activate && timeout 5 streamlit run web/app.py --server.port 8501 --server.address 127.0.0.1 2>&1 || true
      # Expected: starts successfully. Timeout kills it after 5s.
    </automated>
  </verify>
  <done>
    Streamlit app starts without import errors; auth page renders; settings page shows all 7 function slots with model options
  </done>
</task>

---

## Plan 02: Mock Pipeline - Composer + Branding + SRT (Wave 1)

**Objective**: Implement the FFmpeg-based video composer in mock mode, create branding template assets, and implement SRT subtitle generation.

**Purpose**: This is the core of Phase 1 -- the mock pipeline must produce a playable video entirely with local FFmpeg processing, no API keys required. This is the vertical slice that makes Phase 1 deliverable.

**Output**: A working `services/composer.py` that produces a playable 9:16 MP4 with mock digital human, mock B-roll, mock voiceover, SRT subtitles, branding (intro/outro/watermark), and BGM.

### Task 2.1: Create branding template assets and mock media placeholders

<task type="auto">
  <name>Create branding template assets (placeholder images, audio, font)</name>
  <files>
    templates/branding/intro.mp4
    templates/branding/outro.mp4
    templates/branding/watermark.png
    templates/branding/avatar_placeholder.png
    templates/branding/broll_placeholder.png
    templates/music/bgm.mp3
  </files>
  <action>
    Create branding and placeholder assets using FFmpeg and Python imaging.

    Since FFmpeg is available on the system, generate assets programmatically:

    1. `templates/branding/intro.mp4` (3 seconds):
       - Use FFmpeg to create a solid color video with text overlay
       - Background: dark blue (#1a1a2e) or similar
       - Text: "攸县有话说" centered
       - Resolution: 1080x1920 (9:16)

       ```bash
       # Create intro with FFmpeg drawtext
       ffmpeg -y -f lavfi -i color=c=#1a1a2e:s=1080x1920:d=3:r=25 \
         -vf "drawtext=text='攸县有话说':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
         -c:v libx264 -pix_fmt yuv420p templates/branding/intro.mp4
       ```

    2. `templates/branding/outro.mp4` (3 seconds):
       - Similar to intro but with text: "感谢观看"
       - Background: dark green (#1a2e1a) or similar

    3. `templates/branding/watermark.png`:
       - Create using Python (PIL/Pillow) if available, or use a simple ffmpeg approach
       - Simple 200x60 PNG with text: "攸县有话说" (white on transparent)
       - Since we can't rely on PIL being installed, create using ImageMagick or a canvas approach:
       ```bash
       python3 -c "
       import struct, zlib
       # Create minimal 200x60 RGBA PNG with text-like pattern
       # Actually, use ffmpeg to generate a PNG from a solid color frame
       # then create a very simple PNG with drawtext
       "
       ```
       If PIL is not available, create the watermark as a minimal valid PNG file. The actual watermark visual can be simple since this is Phase 1 mock mode.

    4. `templates/branding/avatar_placeholder.png`:
       - Create a 1080x1920 placeholder image showing "数字人占位" text
       - Use FFmpeg drawtext to a single frame:
       ```bash
       ffmpeg -y -f lavfi -i color=c=#2d2d2d:s=1080x1920:d=1 \
         -vf "drawtext=text='数字人占位':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
         -vframes 1 templates/branding/avatar_placeholder.png
       ```

    5. `templates/branding/broll_placeholder.png`:
       - Create a 1080x1920 placeholder image showing "B-roll占位" text
       - Similar approach with different background color (#2d2d3d)

    6. `templates/music/bgm.mp3`:
       - Generate a short silent audio file or use ffmpeg to create a simple tone:
       ```bash
       ffmpeg -y -f lavfi -i "sine=frequency=220:duration=30" -ac 1 -ar 44100 \
         templates/music/bgm.mp3
       ```
       This creates a 30-second 220Hz sine wave as placeholder BGM.

    CRITICAL: All assets must be generated programmatically - no external download, no manual creation. Use FFmpeg filters exclusively. If a specific FFmpeg filter (like drawtext) requires a font, reference an absolute path to a system font (Noto Sans SC or similar), or fall back to a simpler approach without text.

    IMPORTANT: If drawtext fails due to missing font config, skip the text overlay and just create solid color assets. The visual text is cosmetic in Phase 1 - the functional test is that the video plays, not that specific text appears. Document in the SUMMARY what was skipped and why.
  </action>
  <verify>
    <automated>
      ls -la templates/branding/intro.mp4 templates/branding/outro.mp4 templates/branding/watermark.png templates/branding/avatar_placeholder.png templates/branding/broll_placeholder.png templates/music/bgm.mp3
    </automated>
  </verify>
  <done>
    All template assets exist and are valid media files; intro/outro are playable MP4s; watermark is valid PNG; bgm is playable audio
  </done>
</task>

### Task 2.2: Implement FFmpeg composer with mock mode and SRT generator

<task type="auto">
  <name>Implement services/composer.py with mock pipeline and SRT generation</name>
  <files>
    services/composer.py
  </files>
  <action>
    Implement the complete mock video composition pipeline. This is the core deliverable of Phase 1.

    The composer must produce a playable 9:16 video entirely via local FFmpeg processing (no external API calls). It combines:
    - Mock digital human (static image with Ken Burns zoompan effect)
    - Mock B-roll (multiple images with timed overlay, fade transitions)
    - Mock voiceover (silence or generated placeholder audio)
    - Auto-generated SRT subtitles burned into video
    - Branding (watermark overlay, intro/outro clips concatenated)
    - Background music mixed with voiceover

    Implementation details:

    ```python
    import os
    import subprocess
    import tempfile
    import json
    from pathlib import Path


    def compose_mock_video(
        output_path: str = "output/final/mock_demo.mp4",
        duration: float = 15.0,
        voiceover_duration: float = 12.0,
        subtitle_texts: list[dict] = None,
    ) -> str:
        """Generate mock video using only local FFmpeg (no API calls).

        Args:
            output_path: path for the output MP4
            duration: total video duration in seconds
            voiceover_duration: duration of voiceover audio (may be shorter than total)
            subtitle_texts: list of {start, end, text} dicts for SRT subtitles

        Returns:
            Path to the output file
        """
        ...
    ```

    The pipeline should:
    1. Create mock voiceover: generate sine wave or silence audio for `voiceover_duration` seconds
    2. Create mock digital human: apply zoompan to avatar_placeholder.png, loop for `duration` seconds
    3. Create mock B-roll clips: for each image in broll_images list, apply zoompan with timed enable overlay
    4. Generate SRT from subtitle_texts (or default demo subtitles about Youxian)
    5. Overlay watermark PNG
    6. Concatenate intro.mp4 + main content + outro.mp4
    7. Mix voiceover + BGM (bgm.mp3 at volume 0.15)
    8. Output 1080x1920 at 25fps, libx264 + aac

    Key design decisions:
    - Use subprocess.run() with filter_complex for reliability (not ffmpeg-python wrapper)
      - Reason per tech spec section II and RESEARCH.md Pitfall 1: ffmpeg-python 0.2.0 has limited support for complex filter_compose chains with timed enable expressions. Direct filter_complex is more reliable.
      - CRITICAL: Still include `import ffmpeg` in imports so the module is importable, but use subprocess for actual FFmpeg calls
    - Use tempfile.mkdtemp() for intermediate files, clean up in finally
    - Use atomic temp dir: prefix="youxian_compose_"
    - All paths relative to project root (or use Path(__file__).parent.parent)
    - Ken Burns zoom: z='min(zoom+0.0015,1.5)' for digital human, z='min(zoom+0.002,1.3)' for B-roll
    - SRT subtitle font: NotoSansSC with fallback, force_style with FontName, FontSize, PrimaryColour, OutlineColour
    - BGM volume: 0.15 (quiet background)
    - amix filter: duration="first" (voiceover drives duration)

    Helper functions:
    - `_seconds_to_srt_time(seconds: float) -> str`: convert to HH:MM:SS,mmm
    - `_generate_srt(subtitles: list[dict]) -> str`: generate full SRT content
    - `_create_mock_audio(duration: float, output_path: str) -> str`: generate sine wave or silence audio via FFmpeg
    - `_run_ffmpeg(cmd: list[str])`: wrapper for subprocess.run with error handling

    Default subtitles for demo (use if subtitle_texts is None):
    ```python
    DEFAULT_SUBTITLES = [
        {"start": 1.0, "end": 4.0, "text": "大家好，我系攸县人"},
        {"start": 4.5, "end": 8.0, "text": "今天我们来聊一聊攸县米粉"},
        {"start": 8.5, "end": 11.0, "text": "恰得好，耍得欢，攸县米粉最好呷"},
    ]
    ```

    The `compose_video` function (from tech spec section 4.7) signature should also be implemented as the primary public API:
    ```python
    def compose_video(
        digital_human_path: str,
        voice_path: str,
        b_roll_clips: list[dict],
        subtitles: list[dict],
        bgm_path: str,
        branding_path: str,
        output_path: str,
        format: str = "9:16"
    ) -> str:
        ...
    ```
    
    This function does the full real composition with provided inputs. The `compose_mock_video` function calls it with mock-generated inputs.

    For Phase 1, both functions must work without any external API keys. The mock path generates its own audio, and uses the placeholder images from templates/branding/.

    CRITICAL - FFmpeg filter_complex string construction:
    - Build the filter graph as a list of filter strings
    - Final filter chain should look like:
      ```
      [0:v]zoompan=z=...:d=...:s=1080x1920:fps=25[v0];
      [1:v]zoompan=z=...:d=...:s=1080x1920:fps=25,fade=t=in:st=0:d=0.5,fade=t=out:st=...:d=0.5[v1];
      [v0][v1]overlay=enable='between(t,5,8)'[v2];
      [v2]subtitles=subs.srt:force_style='...'[v3];
      [v3][2:v]overlay=W-w-20:H-h-20[outv];
      [3:a][4:a]amix=inputs=2:duration=first[outa]
      ```

    **Error handling**: If FFmpeg fails, raise a descriptive RuntimeError with the FFmpeg stderr output.
  </action>
  <verify>
    <automated>
      source venv/bin/activate && python3 -c "
from services.composer import compose_mock_video, compose_video, _generate_srt, _seconds_to_srt_time
# Test SRT generation
srt = _generate_srt([{'start': 1.0, 'end': 4.5, 'text': 'test'}])
assert '00:00:01,000' in srt
assert '00:00:04,500' in srt
print('OK: SRT generation works')
"
    </automated>
  </verify>
  <done>
    Composer module importable; compose_mock_video runs without errors; SRT generation produces valid output; compose_video function exists with correct signature
  </done>
</task>

### Task 2.3: Run mock pipeline end-to-end, verify playable video output

<task type="auto">
  <name>Run mock pipeline and verify output is a playable video</name>
  <files>
    output/final/.gitkeep
  </files>
  <action>
    Execute the mock pipeline and verify the output video:
    1. Run `compose_mock_video()` to produce a demo video
    2. Use ffprobe to verify: duration, resolution, codecs, file validity
    3. The output must be a valid MP4 with expected properties

    Run from project root:
    ```bash
    
    source venv/bin/activate
    python3 -c "
    from services.composer import compose_mock_video
    result = compose_mock_video(output_path='output/final/mock_demo.mp4')
    print(f'Output: {result}')
    "
    ```

    Then verify with ffprobe:
    ```bash
    ffprobe -v error -show_entries format=duration,format_name -show_entries stream=codec_type,codec_name,height,width output/final/mock_demo.mp4
    ```

    Expected properties:
    - Duration: ~15 seconds (or close to the configured duration)
    - Format: mp4
    - Video codec: h264 (libx264)
    - Audio codec: aac
    - Resolution: 1080x1920 (9:16)
    - File size: reasonable (> 100KB for a 15s video)

    If the pipeline fails:
    - Check FFmpeg error output
    - Verify all template assets exist and are valid
    - Fix filter_complex syntax issues
    - Fix zoompan duration calculation (d is in FRAMES, not seconds -- multiply by fps)
    - Fix subtitles path escaping (colons in paths on Linux)
    - Retry after fix

    CRITICAL: If subprocess-based FFmpeg is unreliable for certain filter chains, fall back to a simpler approach: generate each layer separately (intro, digital human, B-roll, outro) then concatenate. The important thing is producing a PLAYABLE video, not using the most complex filter chain.
  </action>
  <verify>
    <automated>
      ffprobe -v error -show_entries format=duration,format_name output/final/mock_demo.mp4 2>&1
    </automated>
  </verify>
  <done>
    Output file plays correctly with ffprobe/ffplay; duration ~15s; resolution 1080x1920; video h264, audio aac; file size > 100KB
  </done>
</task>

---

## Plan 04: Tests (Wave 2)

**Objective**: Write pytest tests for model_registry and mock pipeline verification.

**Dependency**: Plan 01 (config modules must exist) + Plan 02 (composer must exist)

### Task 4.1: Create model_registry tests

<task type="auto" tdd="true">
  <name>Create pytest tests for ModelRegistry</name>
  <files>
    tests/__init__.py
    tests/conftest.py
    tests/test_model_registry.py
  </files>
  <behavior>
    - test_get_active_returns_model: ModelRegistry.get_active("text_llm") returns ModelOption with correct id
    - test_switch_changes_active: After switch, get_active returns the new model
    - test_switch_invalid_raises: Switching to nonexistent model raises ValueError
    - test_snapshot_immutable: Snapshot is a copy, not the same reference
    - test_update_model_config: update_model_config saves overrides that get_active applies
    - test_list_all_returns_all_slots: list_all() returns all 7 function slots
    - test_model_option_dataclass: ModelOption has all required fields with correct types
  </behavior>
  <action>
    Create test files with fixtures in conftest.py:
    - `monkeypatch.setattr(ModelRegistry, 'STATE_FILE', str(tmp_path / 'model_state.json'))` to isolate tests
    - Each test follows the AAA pattern (Arrange-Act-Assert)
    - Use `tmp_path` fixture for temp directories
    - Use `monkeypatch` fixture for env var overrides
    - All tests must pass with `pytest -x -q`

    CRITICAL: Do NOT modify model_registry.py to make tests pass. Tests must pass against the existing implementation. If a test fails because the implementation is wrong, fix the implementation.
  </action>
  <verify>
    <automated>
      source venv/bin/activate && python3 -m pytest tests/test_model_registry.py -x -q 2>&1
    </automated>
  </verify>
  <done>
    All model_registry tests pass; pytest -x -q exits 0; at least 7 test functions covering all ModelRegistry methods
  </done>
</task>

### Task 4.2: Create mock pipeline test

<task type="auto" tdd="true">
  <name>Create pytest tests for mock pipeline verification</name>
  <files>
    tests/test_mock_pipeline.py
  </files>
  <behavior>
    - test_mock_pipeline_creates_video: compose_mock_video produces a file that exists and ffprobe validates
    - test_mock_pipeline_has_correct_resolution: Output video is 1080x1920 (9:16)
    - test_mock_pipeline_no_api_keys: Mock pipeline runs without any API keys set (CHECK-01)
    - test_generate_srt_valid_format: _generate_srt produces valid SRT format
    - test_seconds_to_srt_time: _seconds_to_srt_time converts correctly
  </behavior>
  <action>
    Create test_mock_pipeline.py with:
    - `conftest` fixture for project root path (use Path to resolve template paths)
    - test_mock_pipeline_creates_video: run compose_mock_video() with temp output path, assert file exists, use ffprobe to validate
    - test_mock_pipeline_has_correct_resolution: ffprobe output shows 1080x1920
    - test_mock_pipeline_no_api_keys: monkeypatch.delenv all API-related env vars, then run compose_mock_video() -- must succeed
    - test_generate_srt_valid_format: input list of dicts, output string with proper SRT numbering and time format
    - test_seconds_to_srt_time: 1.0 -> "00:00:01,000", 3661.5 -> "01:01:01,500"

    For the test that actually runs FFmpeg:
    - Use a SHORT duration (3 seconds instead of 15) to keep tests fast
    - Use pytest.mark.slow for the FFmpeg test so it can be skipped with -m "not slow"
    - Check for ffmpeg availability at test time with `shutil.which("ffmpeg")`

    The no-api-keys test is critical for CHECK-01:
    ```python
    def test_mock_pipeline_no_api_keys(monkeypatch, tmp_path):
        """Mock pipeline must run without ANY API keys configured."""
        # Clear all .env variables that settings.py would load
        for key in ['DEEPSEEK_API_KEY', 'MINIMAX_API_KEY', 'MIMO_API_KEY',
                    'HEYGEN_API_KEY', 'RUNWAY_API_KEY', 'OPENAI_API_KEY',
                    'ANTHROPIC_API_KEY', 'OPENAI_RELAY_API_KEY', 'ADMIN_PASSWORD']:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv('ADMIN_PASSWORD', 'test_pass')

        output = tmp_path / 'mock_no_keys.mp4'
        result = compose_mock_video(output_path=str(output), duration=3.0)
        assert Path(result).exists()
        assert Path(result).stat().st_size > 100_000  # at least 100KB
    ```
  </action>
  <verify>
    <automated>
      source venv/bin/activate && python3 -m pytest tests/test_mock_pipeline.py -x -q -m "not slow" 2>&1
    </automated>
  </verify>
  <done>
    All mock pipeline tests pass; test_mock_pipeline_no_api_keys confirms CHECK-01 (no API keys needed); test_mock_pipeline_creates_video produces playable output
  </done>
</task>

---

## Success Criteria (Phase 1)

1. `scripts/setup.sh` creates working venv with all dependencies -- PASS via Plan 01 Task 1.2
2. Models configurable via model_registry.py -- PASS via Plan 01 Task 1.1
3. Full mock pipeline produces a playable video file -- PASS via Plan 02 Task 2.3
4. Video includes: mock digital human, mock B-roll, mock voiceover, subtitles, branding, BGM -- PASS via Plan 02 Task 2.3
5. `pytest tests/test_model_registry.py` passes -- PASS via Plan 04 Task 4.1
6. Mock pipeline runs without paid API keys -- PASS via Plan 04 Task 4.2 (CHECK-01)
7. Streamlit settings page shows model registry -- PASS via Plan 01 Task 1.3
