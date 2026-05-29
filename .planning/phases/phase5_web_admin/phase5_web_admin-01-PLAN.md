---
phase: 05-web_admin
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - youxianduanshipin/web/app.py
  - youxianduanshipin/web/pages/settings.py
  - youxianduanshipin/web/pages/create.py
  - youxianduanshipin/web/pages/review.py
  - youxianduanshipin/web/pages/publish.py
  - youxianduanshipin/web/pages/dashboard.py
  - youxianduanshipin/web/models.py
  - youxianduanshipin/tests/test_web_admin.py
autonomous: true
requirements: [WEB-03, WEB-05, WEB-06, WEB-07, WEB-08, WEB-09, CHECK-03, CHECK-04]
user_setup: []
must_haves:
  truths:
    - "User can create a new video topic by entering an idea, see AI-diverge results, and confirm a topic"
    - "User can review a storyboard with shot-by-shot preview, see video playback, approve/reject with structured revision dimensions"
    - "User can view pending publish queue, select platforms, schedule time, and confirm publish (check-first mode)"
    - "User can view dashboard with follower trends, top videos list, and weekly report"
    - "User can see full lifecycle tracking of any video (idea -> published) and has retry button for any failed stage"
    - "User can manage model settings (existing) plus review settings page enhancements"
    - "Navigation includes all 5 pages: create, review, publish, dashboard, settings"
  artifacts:
    - path: "youxianduanshipin/web/app.py"
      provides: "Streamlit entrypoint with all 5 page navigation"
      min_lines: 60
    - path: "youxianduanshipin/web/pages/create.py"
      provides: "Topic creation page: idea input, AI diverge, topic confirmation"
      min_lines: 100
    - path: "youxianduanshipin/web/pages/review.py"
      provides: "Review page: storyboard preview, video playback, approve/reject with structured revision"
      min_lines: 150
    - path: "youxianduanshipin/web/pages/publish.py"
      provides: "Publish page: pending queue, platform select, schedule, confirm-first publish"
      min_lines: 120
    - path: "youxianduanshipin/web/pages/dashboard.py"
      provides: "Dashboard page: follower trends, top videos, weekly report"
      min_lines: 100
    - path: "youxianduanshipin/web/pages/settings.py"
      provides: "Enhanced settings with lifecycle tracking table"
      min_lines: 140
    - path: "youxianduanshipin/web/models.py"
      provides: "Updated Pydantic models for lifecycle tracking"
      min_lines: 200
    - path: "youxianduanshipin/tests/test_web_admin.py"
      provides: "Tests for all admin pages"
      min_lines: 80
  key_links:
    - from: "web/app.py"
      to: "web/pages/create.py"
      via: "st.Page() import and st.navigation()"
      pattern: "from web.pages.create import|st.Page.*create"
    - from: "web/pages/create.py"
      to: "agents/content_agent"
      via: "ContentAgent.diverge_topics() call"
      pattern: "ContentAgent"
    - from: "web/pages/review.py"
      to: "web/database.py"
      via: "get_db_connection() for video/script/storyboard data"
      pattern: "get_db_connection"
    - from: "web/pages/publish.py"
      to: "web/database.py"
      via: "get_db_connection() for publish_queue table"
      pattern: "publish_queue"
    - from: "web/pages/dashboard.py"
      to: "web/database.py"
      via: "get_db_connection() for analytics_data table"
      pattern: "analytics_data"
    - from: "web/pages/settings.py"
      to: "web/database.py"
      via: "get_db_connection() for lifecycle videos query"
      pattern: "videos.*status"
---

<objective>
Complete the Streamlit web admin backend with all 5 pages (create, review, publish, dashboard, settings) plus lifecycle tracking, allowing the user to fully manage the video production workflow from idea to published video via the web interface.

Purpose: This is the final integration phase that connects agents, services, and database into a usable web admin. After this phase, the MVP admin workflow is complete (create -> produce -> review -> publish -> analyze).
Output: 5 Streamlit admin page modules, updated app.py with navigation, updated models.py with lifecycle tracking fields, and admin page tests.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md

@youxianduanshipin/web/app.py
@youxianduanshipin/web/pages/settings.py
@youxianduanshipin/web/auth.py
@youxianduanshipin/web/database.py
@youxianduanshipin/web/models.py
@youxianduanshipin/web/routers/topics.py
@youxianduanshipin/web/routers/scripts.py
@youxianduanshipin/web/routers/videos.py
@youxianduanshipin/agents/content_agent.py
@youxianduanshipin/agents/ops_agent.py
@youxianduanshipin/agents/production_agent.py
@youxianduanshipin/services/publisher.py
@youxianduanshipin/config/prompts.py
@youxianduanshipin/config/model_registry.py
@youxianduanshipin/scripts/init_db.py
@youxianduanshipin/tests/conftest.py

<interfaces>

From web/database.py:
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

From agents/content_agent.py:
```python
class ContentAgent:
    def __init__(self):
        self.llm = text_llm

    async def diverge_topics(self, user_idea: str, count: int = 5) -> list[dict]:
        """发散多个角度的选题"""
        # Returns list of dicts with keys: title, pillar, difficulty, heat_prediction

    async def generate_script(self, topic: dict, dialect_dict: list = None) -> dict:
        """根据选题生成完整脚本"""
```

From agents/ops_agent.py:
```python
class OpsAgent:
    async def publish_approved(self, video_path, platforms, title="", tags=None, description="") -> dict:
    async def collect_daily_data(self) -> dict:
    async def generate_weekly_report(self, raw_data=None) -> dict:
```

From config/prompts.py:
```python
# REVISION_PARSE_PROMPT — parses NL feedback into structured operations
# Actions: retake_shot, edit_subtitle, change_bgm, adjust_voice, trim, reschedule
```

From web/auth.py:
```python
def check_auth():
    # Streamlit auth guard, call before page navigation
```

From web/models.py VALID_TRANSITIONS state machine:
```
idea -> topic_selected -> script_ready -> storyboard_ready -> voice_ready ->
avatar_ready -> broll_ready -> composing -> composed -> pending_review ->
approved -> publishing -> published
rejected -> script_ready | topic_selected
```

From scripts/init_db.py tables:
- videos: id, title, status, topic_id, script_id, storyboard_id, dialect_dictionary, fact_risk_level, created_at, updated_at
- topics: id, video_id, title, pillar, source, status, created_at
- scripts: id, video_id, content, title, dialect_words, status, fact_check_notes, created_at
- storyboards: id, video_id, shots, status, created_at
- model_call_logs: id, job_id, task_type, model_id, provider, channel, prompt_version, input_tokens, output_tokens, latency_ms, cost_estimate, success, error_message, quality_score, created_at
- publish_queue: id, video_id, platform, status, scheduled_at, published_at, platform_post_id, error_message, retry_count, created_at
- analytics_data: id, video_id, platform, date, views, likes, comments, shares, followers, collected_at

</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update web/models.py with lifecycle tracking fields (per WEB-03, CHECK-03)</name>
  <files>
    youxianduanshipin/web/models.py
  </files>
  <action>
    Add the following to web/models.py:

    1. Add a `VideoLifecycleResponse` Pydantic model with fields:
       - id: int
       - title: str
       - status: str
       - topic_id: Optional[int]
       - script_id: Optional[int]
       - storyboard_id: Optional[int]
       - fact_risk_level: str
       - created_at: str
       - updated_at: str
       - topic_title: Optional[str] (join from topics table)
       - script_title: Optional[str] (join from scripts table)
       - last_publish_platform: Optional[str] (join from publish_queue)
       - last_publish_status: Optional[str] (join from publish_queue)
       - retry_count: Optional[int] (from publish_queue)
       model_config = {"from_attributes": True}

    2. Add `PublishQueueResponse` model with fields:
       - id, video_id, platform, status, scheduled_at, published_at, platform_post_id, error_message, retry_count, created_at
       - video_title: Optional[str] (joined)
       model_config = {"from_attributes": True}

    3. Add `AnalyticsTrendResponse` model with fields:
       - date: str
       - platform: str
       - views, likes, comments, shares, followers: int

    4. Add `WeeklyReportResponse` model with:
       - report_date: str
       - summary: str
       - top_videos: list[dict]
       - recommendations: list[str]

    5. Add `ReviewAction` Pydantic model with fields matching the revision_parser output:
       - type: str (enum: retake_shot, edit_subtitle, change_bgm, adjust_voice, trim, reschedule)
       - target_shot: Optional[str]
       - instruction: str

    6. Add `ReviewResponse` model with:
       - video_id: int
       - action: Literal["approve", "reject"]
       - revision_notes: Optional[str]
       - revision_actions: Optional[list[ReviewAction]]

    Keep all existing models. Append at the end of the file after line 193.
  </action>
  <verify>
    <automated>python -c "from web.models import VideoLifecycleResponse, PublishQueueResponse, AnalyticsTrendResponse, WeeklyReportResponse, ReviewAction, ReviewResponse; print('All new models imported successfully')"</automated>
  </verify>
  <done>All 6 new Pydantic models exist and import without errors</done>
</task>

<task type="auto">
  <name>Task 2: Create web/pages/create.py — topic diverge + confirm page (per WEB-05)</name>
  <files>
    youxianduanshipin/web/pages/create.py
  </files>
  <action>
    Create a Streamlit page at `web/pages/create.py` with render function `render_create_page()`.

    The page implements the "topic -> idea -> AI diverge -> confirm" workflow per WEB-05:

    1. **Page title:** "选题共创" with caption "输入选题想法，AI自动发散多角度选题，确认后进入制作流程"

    2. **Step 1 — Input user idea:**
       - `st.text_area("输入你的选题想法", height=100, placeholder="例：攸县米粉为什么这么出名")`
       - `st.slider("发散数量", min_value=3, max_value=10, value=5)`
       - Button "AI发散选题" labeled "开始发散"

    3. **Step 2 — AI diverge (async):**
       - When "开始发散" clicked, show spinner via `st.spinner("AI正在发散选题...")`
       - Import `agents.ContentAgent` and call `agent.diverge_topics(user_idea, count)` asynchronously
       - Use `asyncio.run()` since Streamlit runs in sync context
       - Handle errors: if ContentAgent not available (no API key), show `st.warning("未配置API密钥，使用模拟数据")` and generate 3-5 hardcoded sample topics for demonstration
       - Display results as cards: each topic shows title, pillar badge (color-coded: 美食/green, 风俗/orange, 景点/blue, 故事/purple), difficulty stars, heat prediction stars

    4. **Step 3 — Confirm topic:**
       - Each topic card has an "选定该选题" button
       - When confirmed, store in `st.session_state.confirmed_topic`
       - Call FastAPI to create video and topic records:
         - POST `/api/videos/` with `{"title": topic_title}`
         - POST `/api/topics/` with `{"video_id": id, "title": topic_title, "pillar": pillar}`
         - PUT `/api/videos/{id}/status` with `{"status": "topic_selected"}`
       - Since async HTTP calls within Streamlit are tricky, use `asyncio.run()` wrapping `httpx.AsyncClient` calls
       - Or use `requests` synchronously — simpler for Streamlit
       - Show `st.toast("✅ 选题已确认，进入脚本生成阶段")`

    5. **Already confirmed state:**
       - If `st.session_state.confirmed_topic` exists, show the confirmed topic info and a button to "开始新选题" to reset

    6. **Lifecycle link (per CHECK-03):**
       - At bottom of page, show a small expander "查看已有选题列表"
       - Use `asyncio.run(get_db_connection())` to query `SELECT v.id, v.title, v.status, t.title as topic_title FROM videos v LEFT JOIN topics t ON v.topic_id = t.id ORDER BY v.created_at DESC LIMIT 20`
       - Display in a `st.dataframe` with columns: ID, 标题, 状态, 选题

    7. Handle exceptions gracefully — wrap all DB/API calls in try/except with `st.error()`.

    Use st.Page-compatible function signature. The function `render_create_page()` takes no arguments.
  </action>
  <verify>
    <automated>python -c "import ast; ast.parse(open('youxianduanshipin/web/pages/create.py').read()); print('Syntax OK')"</automated>
  </verify>
  <done>File exists, parses without syntax errors, render_create_page() is exported</done>
</task>

<task type="auto">
  <name>Task 3: Create web/pages/review.py — storyboard preview + video playback + approve/reject (per WEB-06)</name>
  <files>
    youxianduanshipin/web/pages/review.py
  </files>
  <action>
    Create a Streamlit page at `web/pages/review.py` with render function `render_review_page()`.

    The page implements the review center per WEB-06: storyboard preview, video playback, approve/reject with structured revision dimensions.

    1. **Page title:** "审核中心" with caption "预览分镜/视频，通过或驳回并给出结构化修改意见"

    2. **Video selector:**
       - Query DB for videos with status `pending_review` via `asyncio.run(get_db_connection())`:
         `SELECT v.*, s.content as script_content, sb.shots as storyboard_shots
          FROM videos v
          LEFT JOIN scripts s ON v.script_id = s.id
          LEFT JOIN storyboards sb ON v.storyboard_id = sb.id
          WHERE v.status = 'pending_review'`
       - If none, show `st.info("暂无待审核视频")`
       - If multiple, `st.selectbox("选择待审核视频", options, format_func=lambda r: f"#{r['id']} {r['title']}")`
       - Store selected video in session state

    3. **Storyboard preview section:**
       - Show `st.subheader("分镜预览")`
       - Parse `shots` from storyboard JSON string
       - For each shot, display:
         - `st.markdown(f"**镜头 {shot['shot_id']}** — {shot.get('type', 'N/A')} ({shot.get('duration', 0)}s)")`
         - `st.markdown(f"画面: {shot.get('visual_description', 'N/A')}")`
         - `st.markdown(f"台词: {shot.get('dialogue', 'N/A')}")`
       - Use `st.expander` per shot or `st.columns` for layout

    4. **Video playback section:**
       - Look for video file in `output/final/` directory matching this video's id pattern
       - If found, show `st.video(video_path)`
       - If not found, show `st.info("视频文件暂未生成 — 需要先执行制作流程")` with a "触发制作" button
       - "触发制作" button calls `ContentAgent.generate_script()` then `ProductionAgent.produce_single()` via `asyncio.run()`

    5. **Script preview:**
       - `st.subheader("脚本内容")`
       - Show script content in a `st.text_area` (read-only via `disabled=True`)

    6. **Approve/Reject section (per tech spec 6.3):**
       - `st.radio("审核结果", ["通过", "驳回"])`
       - If "通过":
         - `st.text_area("审核备注（可选）", placeholder="例：整体质量不错，可直接发布")`
         - Button "确认通过": updates status to `approved` via PUT `/api/videos/{id}/status`
       - If "驳回" (show structured revision form per WEB-06/6.3 dimensions):
         - Dimension 1 — `st.selectbox("修改维度", ["脚本内容", "方言准确性", "视觉效果", "音频质量", "时长控制", "其他"])`
         - Dimension 2 — `st.selectbox("修改级别", ["微调（可自动修复）", "重做部分镜头", "全部重做"])`
         - `st.text_area("具体修改要求", height=100, placeholder="例：第二个镜头画面不够生动，需要替换成更热闹的街景")`
         - Button "提交驳回意见":
           - Updates status to `rejected` via PUT `/api/videos/{id}/status`
           - If revision notes exist, optionally call `RevisionParser.parse_revision()` from `agents.revision_parser` to get structured actions (best-effort, fallback if LLM unavailable)
           - Store revision notes in UI if no API to store them yet

    7. **Reviewed history:**
       - At bottom, show a small expander "审核历史"
       - Query `SELECT id, title, status, updated_at FROM videos WHERE status IN ('approved', 'rejected') ORDER BY updated_at DESC LIMIT 10`
       - Show in `st.dataframe`

    Use `asyncio.run(get_db_connection())` for DB queries (sync context). Import `agents.ContentAgent`, `agents.ProductionAgent` for triggers.
  </action>
  <verify>
    <automated>python -c "import ast; ast.parse(open('youxianduanshipin/web/pages/review.py').read()); print('Syntax OK')"</automated>
  </verify>
  <done>File exists, parses without syntax errors, render_review_page() is exported</done>
</task>

<task type="auto">
  <name>Task 4: Create web/pages/publish.py — pending queue + confirm-first publish (per WEB-07, CHECK-04)</name>
  <files>
    youxianduanshipin/web/pages/publish.py
  </files>
  <action>
    Create a Streamlit page at `web/pages/publish.py` with render function `render_publish_page()`.

    The page implements the publish management per WEB-07 and CHECK-04 (confirm-first publish mode).

    1. **Page title:** "发布管理" with caption "管理待发布视频，选择平台和发布时间，确认后发布"

    2. **Pending queue section:**
       - Query DB for `publish_queue` with pending status:
         `SELECT pq.*, v.title as video_title FROM publish_queue pq JOIN videos v ON pq.video_id = v.id WHERE pq.status = 'pending' ORDER BY pq.created_at DESC`
       - Also query approved videos not yet in publish_queue:
         `SELECT v.id, v.title FROM videos v WHERE v.status = 'approved' AND v.id NOT IN (SELECT video_id FROM publish_queue WHERE status != 'cancelled')`
       - Display pending queue as a table with columns: ID, 视频标题, 平台, 计划发布时间, 状态
       - For each row, show action buttons in the same row via columns layout

    3. **Add to queue section:**
       - If approved videos exist without queue entries:
         - `st.subheader("添加发布任务")`
         - `st.selectbox("选择视频", options_from_approved)`
         - `st.multiselect("发布平台", ["douyin", "kuaishou", "weixin", "xiaohongshu"], default=["douyin"])`
         - Platform names displayed in Chinese with mapping: douyin→抖音, kuaishou→快手, weixin→视频号, xiaohongshu→小红书
         - `st.date_input("计划发布日期", value="today")`
         - `st.time_input("计划发布时间", value="now")`
         - Button "加入发布队列":
           - Inserts into `publish_queue` table for each selected platform
           - Uses `asyncio.run(get_db_connection())`

    4. **Confirm-first publish (per CHECK-04):**
       - Pending queue items show a two-step flow:
         - Step 1: Review item details (video title, platforms, schedule)
         - Step 2: Button "确认并发布" — labeled as "确认并发布（不可撤回）"
         - On click:
           - Update `publish_queue` status to `publishing`
           - Call `OpsAgent().publish_approved()` via `asyncio.run()`
           - Update status to `published` or `failed`
           - Update video status to `published`
           - Show `st.toast()` with result
         - A separate "取消" button to set queue status to `cancelled`

    5. **Published history:**
       - `st.subheader("发布历史")`
       - Query `SELECT pq.*, v.title as video_title FROM publish_queue pq JOIN videos v ON pq.video_id = v.id WHERE pq.status IN ('published', 'failed', 'cancelled') ORDER BY pq.created_at DESC LIMIT 20`
       - Show in `st.dataframe` with colored status badges

    6. **Retry failed publishes (per CHECK-03 lifecycle tracking):**
       - For items with status `failed`, show a "重试" button
       - On click, update status back to `pending` and repeat confirm-first flow

    Handle all DB operations via `asyncio.run(get_db_connection())`. Use proper error handling for each step.
  </action>
  <verify>
    <automated>python -c "import ast; ast.parse(open('youxianduanshipin/web/pages/publish.py').read()); print('Syntax OK')"</automated>
  </verify>
  <done>File exists, parses without syntax errors, render_publish_page() is exported</done>
</task>

<task type="auto">
  <name>Task 5: Create web/pages/dashboard.py — analytics trends + top videos + weekly report (per WEB-08)</name>
  <files>
    youxianduanshipin/web/pages/dashboard.py
  </files>
  <action>
    Create a Streamlit page at `web/pages/dashboard.py` with render function `render_dashboard_page()`.

    The page implements the data dashboard per WEB-08: follower trends, top videos, and weekly report. Simulated analytics per design decision (real data collection deferred).

    1. **Page title:** "数据看板" with caption "视频表现概览，粉丝趋势，热门选题，周度分析报告"

    2. **Follower trends section:**
       - `st.subheader("粉丝增长趋势")`
       - Query `analytics_data` table for mock data:
         `SELECT date, platform, SUM(followers) as total_followers FROM analytics_data GROUP BY date ORDER BY date ASC LIMIT 30`
       - If no data exists, generate simulated data:
         - `st.info("暂无实际数据，使用模拟数据展示趋势")`
         - Generate 14 days of mock data with slight upward trend using Python (random module)
         - Store simulated data in session state to persist across reruns
       - Display using `st.line_chart(data, x="date", y="followers", color="platform")`
       - Show platform breakdown below chart

    3. **Top videos section:**
       - `st.subheader("热门视频 TOP 10")`
       - Query or simulate: `SELECT v.title, v.status, COALESCE(SUM(a.views), 0) as total_views FROM videos v LEFT JOIN analytics_data a ON v.id = a.video_id GROUP BY v.id ORDER BY total_views DESC LIMIT 10`
       - Display as a table with rank, title, views, likes, comments
       - If simulated, generate mock view counts

    4. **Weekly report section:**
       - `st.subheader("周度分析报告")`
       - Button "生成周报"
       - On click, use spinner and call `OpsAgent().generate_weekly_report()` via `asyncio.run()`
       - If OpsAgent not available (no API key), generate template report with `st.info("AI周报需要API密钥，显示模板报告")` and show a structured placeholder:
         - 各平台表现概览 (mock data)
         - 热门选题 TOP5 (from topics table)
         - 待改进问题 (generic)
         - 下周策略建议 (generic)
       - Display report in structured format using `st.markdown()`

    5. **Quick stats row:**
       - Top of page, 4 metric cards in `st.columns(4)`:
         - 总视频数: count from videos table
         - 已发布: count where status='published'
         - 待审核: count where status='pending_review'
         - 总粉丝数: sum of followers from analytics_data (or simulated)

    Handle DB queries via `asyncio.run(get_db_connection())`. Import `agents.OpsAgent` for weekly report generation.
  </action>
  <verify>
    <automated>python -c "import ast; ast.parse(open('youxianduanshipin/web/pages/dashboard.py').read()); print('Syntax OK')"</automated>
  </verify>
  <done>File exists, parses without syntax errors, render_dashboard_page() is exported</done>
</task>

<task type="auto">
  <name>Task 6: Update web/pages/settings.py with lifecycle tracking table (per WEB-09, CHECK-03)</name>
  <files>
    youxianduanshipin/web/pages/settings.py
  </files>
  <action>
    Enhance the existing settings page at `web/pages/settings.py` (per WEB-09) by adding a lifecycle tracking section (per CHECK-03) at the bottom.

    1. **Keep existing code** — all model registry forms, test connection buttons, switch/save buttons must remain unchanged.

    2. **Add lifecycle tracking section** at the bottom of `render_settings_page()`, after the existing model registry loop:

       After line 129 (the last `st.divider()` in the main loop), add:

       ```python
       # ── Lifecycle Tracking Section (CHECK-03) ──

       st.title("全生命周期追踪")
       st.caption("从 idea 到发布的全流程追踪，支持任意阶段重试")

       lifecycle_data = _query_lifecycle_data()

       if lifecycle_data:
           for item in lifecycle_data:
               with st.expander(f"#{item['id']} {item['title']} — {item['status']}", expanded=False):
                   cols = st.columns([2, 1, 1, 1])
                   cols[0].markdown(f"**状态:** {item['status']}")
                   cols[1].markdown(f"**创建:** {item['created_at']}")
                   cols[2].markdown(f"**更新:** {item['updated_at']}")
                   cols[3].markdown(f"**风险:** {item.get('fact_risk_level', 'N/A')}")

                   # Show available actions based on current status
                   valid_next = VALID_TRANSITIONS.get(item['status'], [])
                   if valid_next:
                       st.markdown(f"**可执行操作:** {' → '.join(valid_next)}")
                       target_status = st.selectbox(
                           f"选择目标状态 (视频 #{item['id']})",
                           valid_next,
                           key=f"lifecycle_status_{item['id']}"
                       )
                       if st.button(f"推进到 {target_status}", key=f"lifecycle_btn_{item['id']}"):
                           _transition_status(item['id'], target_status)
                   else:
                       st.markdown("**最终状态 — 无更多可执行操作**")

                   # Retry button for failed/pending_review/rejected states
                   if item['status'] in ('rejected',):
                       if st.button("重新制作", key=f"retry_{item['id']}"):
                           _transition_status(item['id'], 'topic_selected')
       else:
           st.info("暂无可追踪的视频数据")

       st.divider()
       ```

    3. **Add helper functions** at module level (before `render_settings_page`):

       ```python
       def _query_lifecycle_data() -> list[dict]:
           """Query all videos with lifecycle information."""
           import asyncio
           from web.database import get_db_connection
           try:
               db = asyncio.run(get_db_connection())
               cursor = db.execute(
                   "SELECT v.*, t.title as topic_title "
                   "FROM videos v "
                   "LEFT JOIN topics t ON v.topic_id = t.id "
                   "ORDER BY v.updated_at DESC LIMIT 50"
               )
               rows = cursor.fetchall()
               db.close()
               return [dict(r) for r in rows]
           except Exception:
               return []

       def _transition_status(video_id: int, target_status: str):
           """Transition video status with state machine validation."""
           import asyncio
           from web.database import get_db_connection
           try:
               db = asyncio.run(get_db_connection())
               cursor = db.execute("SELECT status FROM videos WHERE id=?", (video_id,))
               row = cursor.fetchone()
               if row:
                   from web.models import VALID_TRANSITIONS
                   current = row["status"]
                   if target_status in VALID_TRANSITIONS.get(current, []):
                       db.execute(
                           "UPDATE videos SET status=?, updated_at=datetime('now','localtime') WHERE id=?",
                           (target_status, video_id),
                       )
                       db.commit()
                       st.toast(f"✅ 视频 #{video_id} 状态已更新: {current} → {target_status}")
                   else:
                       st.error(f"不允许的状态转换: {current} → {target_status}")
               db.close()
           except Exception as e:
               st.error(f"状态更新失败: {e}")
       ```

    Insert `_query_lifecycle_data` and `_transition_status` right after the `test_api_connection` function (after line 39), before `render_settings_page`.
  </action>
  <verify>
    <automated>python -c "import ast; ast.parse(open('youxianduanshipin/web/pages/settings.py').read()); print('Syntax OK')"</automated>
  </verify>
  <done>File parses correctly, lifecycle tracking section renders after model registry, _query_lifecycle_data and _transition_status functions exist</done>
</task>

<task type="auto">
  <name>Task 7: Update web/app.py with all 5 admin pages in navigation</name>
  <files>
    youxianduanshipin/web/app.py
  </files>
  <action>
    Update `web/app.py` to register all 5 admin pages in Streamlit navigation.

    Modify the `run_streamlit()` function:

    1. Import all 5 page render functions at the top of `run_streamlit()`:
       ```python
       from web.pages.create import render_create_page
       from web.pages.review import render_review_page
       from web.pages.publish import render_publish_page
       from web.pages.dashboard import render_dashboard_page
       from web.pages.settings import render_settings_page
       ```

    2. Create `st.Page` objects for all 5 pages with icons:
       ```python
       create_page = st.Page(render_create_page, title="选题共创", icon=":material/lightbulb:")
       review_page = st.Page(render_review_page, title="审核中心", icon=":material/rate_review:")
       publish_page = st.Page(render_publish_page, title="发布管理", icon=":material/publish:")
       dashboard_page = st.Page(render_dashboard_page, title="数据看板", icon=":material/bar_chart:")
       settings_page = st.Page(render_settings_page, title="模型设置", icon=":material/settings:")
       ```

    3. Update `st.navigation()` to include all pages:
       ```python
       pg = st.navigation([create_page, review_page, publish_page, dashboard_page, settings_page])
       ```

    4. Keep the existing imports (`check_auth`, `st.set_page_config`) and auth guard intact.

    The updated run_streamlit function should look like:
    ```python
    def run_streamlit():
        st.set_page_config(page_title="攸县有话说", layout="wide", page_icon="🎬")
        check_auth()

        from web.pages.create import render_create_page
        from web.pages.review import render_review_page
        from web.pages.publish import render_publish_page
        from web.pages.dashboard import render_dashboard_page
        from web.pages.settings import render_settings_page

        create_page = st.Page(render_create_page, title="选题共创", icon=":material/lightbulb:")
        review_page = st.Page(render_review_page, title="审核中心", icon=":material/rate_review:")
        publish_page = st.Page(render_publish_page, title="发布管理", icon=":material/publish:")
        dashboard_page = st.Page(render_dashboard_page, title="数据看板", icon=":material/bar_chart:")
        settings_page = st.Page(render_settings_page, title="模型设置", icon=":material/settings:")

        pg = st.navigation([create_page, review_page, publish_page, dashboard_page, settings_page])
        pg.run()
    ```

    Remove the old single-page import and navigation code.
  </action>
  <verify>
    <automated>python -c "import ast; ast.parse(open('youxianduanshipin/web/app.py').read()); print('Syntax OK')"</automated>
  </verify>
  <done>run_streamlit() imports all 5 page functions and registers all 5 pages in st.navigation()</done>
</task>

<task type="auto">
  <name>Task 8: Create tests/test_web_admin.py — tests for all admin pages</name>
  <files>
    youxianduanshipin/tests/test_web_admin.py
  </files>
  <action>
    Create test file at `tests/test_web_admin.py` with the following tests:

    1. **test_create_page_import** — `from web.pages.create import render_create_page` succeeds

    2. **test_review_page_import** — `from web.pages.review import render_review_page` succeeds

    3. **test_publish_page_import** — `from web.pages.publish import render_publish_page` succeeds

    4. **test_dashboard_page_import** — `from web.pages.dashboard import render_dashboard_page` succeeds

    5. **test_settings_page_import** — `from web.pages.settings import render_settings_page, _query_lifecycle_data, _transition_status` succeeds

    6. **test_app_navigation** — Verify that `web/app.py` imports all 5 page render functions (use `ast` module to parse the file and check function names referenced in `st.Page()` calls)

    7. **test_lifecycle_models** — `from web.models import VideoLifecycleResponse, PublishQueueResponse, ReviewAction, ReviewResponse` all import

    8. **test_models_update** — Verify `web/models.py` file length >= 200 lines (has the new models appended)

    9. **test_app_has_all_pages** — Parse `web/app.py` AST and verify 5 `st.Page()` calls exist

    Use `pytest.mark.unit` for all tests. Import fixtures from `conftest.py` as needed.

    The test should NOT run Streamlit (no headless browser). They verify imports, structure, and model availability only.
  </action>
  <verify>
    <automated>python -m pytest tests/test_web_admin.py -x -v</automated>
  </verify>
  <done>All 9 tests pass</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| User browser -> Streamlit server | User input (sensitive: idea text, revision feedback) |
| Streamlit server -> SQLite | Admin writes to production database |
| Streamlit server -> External LLM API | User idea text sent to third-party LLM |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-05-01 | S (Spoofing) | check_auth() gate | mitigate | All pages behind Streamlit auth guard (existing) |
| T-05-02 | T (Tampering) | Lifecycle status transitions | mitigate | State machine validation in _transition_status() — rejects invalid transitions per VALID_TRANSITIONS |
| T-05-03 | I (Info Disclosure) | Dashboard analytics | accept | Only mock/simulated data in Phase 5; real data collection deferred — no PII exposed |
| T-05-04 | E (Elevation) | Cancel/publish actions | mitigate | Confirm-first mode (CHECK-04); publish requires explicit second click; cancel requires explicit action |
</threat_model>

<verification>
1. All 5 new page files exist and are parseable
2. web/app.py registers all 5 pages in st.navigation()
3. web/models.py has 6 new lifecycle models
4. web/pages/settings.py has lifecycle tracking section at bottom
5. All 9 tests pass: pytest tests/test_web_admin.py -x -v
6. `streamlit run web/app.py` starts without import errors (manual verify)

Steps 1-5 are automated. Step 6 is manual (checkpoint).
</verification>

<success_criteria>
1. User can navigate between all 5 admin pages in Streamlit sidebar
2. Create page: user enters idea -> AI diverges topics -> user confirms one -> video/topic records created
3. Review page: user sees pending storyboards -> previews shots/script/video -> approves or rejects with structured revision dimensions
4. Publish page: user sees pending queue -> adds approved videos with platform/schedule -> confirms publish via two-step flow
5. Dashboard page: user sees follower trend chart, top videos table, and can generate weekly report
6. Settings page: user manages models (existing) and sees lifecycle table with retry buttons for any stage
7. Lifecycle tracking: all videos visible in settings page table with status transitions and retry support
8. Confirm-first mode: publish requires explicit confirmation click (not single-click publish)
</success_criteria>

<output>
After completion, create `.planning/phases/05-web_admin/05-01-SUMMARY.md`
</output>
