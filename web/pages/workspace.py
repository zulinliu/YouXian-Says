"""工作台 — 用户首屏枢纽页面，聚合待办、流水线和本周概览。"""
import asyncio
import logging
from datetime import datetime, timedelta

import streamlit as st

from web.styles import (
    COLORS, STATUS_COLORS, PIPELINE_STAGES, PIPELINE_ICONS,
    icon, esc, page_header, task_card, stat_card, empty_state,
    section_header,
)

logger = logging.getLogger(__name__)


# ── 数据查询 ──

def _query_workspace() -> dict:
    """从数据库聚合工作台数据。"""
    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _q():
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row

                # 待审核视频
                cur = await db.execute(
                    "SELECT id, title, status, updated_at FROM videos "
                    "WHERE status='pending_review' ORDER BY updated_at DESC"
                )
                pending_review = [dict(r) for r in await cur.fetchall()]

                # 待发布视频
                cur = await db.execute(
                    "SELECT id, title, status, updated_at FROM videos "
                    "WHERE status='approved' ORDER BY updated_at DESC"
                )
                approved = [dict(r) for r in await cur.fetchall()]

                # 所有进行中的视频（非 published/rejected）
                cur = await db.execute(
                    "SELECT id, title, status, updated_at FROM videos "
                    "WHERE status NOT IN ('published', 'rejected') "
                    "ORDER BY updated_at DESC LIMIT 20"
                )
                in_progress = [dict(r) for r in await cur.fetchall()]

                # 本周统计 — 选题数
                week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                cur = await db.execute(
                    "SELECT COUNT(*) FROM videos WHERE created_at >= ?", (week_ago,)
                )
                row = await cur.fetchone()
                week_topics = row[0] if row else 0

                # 本周审核数
                cur = await db.execute(
                    "SELECT COUNT(*) FROM videos "
                    "WHERE status IN ('approved', 'rejected', 'published') "
                    "AND updated_at >= ?", (week_ago,)
                )
                row = await cur.fetchone()
                week_reviewed = row[0] if row else 0

                # 本周发布数
                cur = await db.execute(
                    "SELECT COUNT(*) FROM videos "
                    "WHERE status='published' AND updated_at >= ?", (week_ago,)
                )
                row = await cur.fetchone()
                week_published = row[0] if row else 0

                # 总视频数
                cur = await db.execute("SELECT COUNT(*) FROM videos")
                row = await cur.fetchone()
                total_videos = row[0] if row else 0

                # 各状态计数
                cur = await db.execute(
                    "SELECT status, COUNT(*) as cnt FROM videos GROUP BY status"
                )
                status_counts = {r[0]: r[1] for r in await cur.fetchall()}

                return {
                    "pending_review": pending_review,
                    "approved": approved,
                    "in_progress": in_progress,
                    "week_topics": week_topics,
                    "week_reviewed": week_reviewed,
                    "week_published": week_published,
                    "total_videos": total_videos,
                    "status_counts": status_counts,
                }

        return asyncio.run(_q())
    except Exception:
        logger.exception("工作台数据查询失败")
        return {
            "pending_review": [], "approved": [], "in_progress": [],
            "week_topics": 0, "week_reviewed": 0, "week_published": 0,
            "total_videos": 0, "status_counts": {},
        }


# ── 阶段中文名映射 ──

STAGE_LABELS = {
    s[0]: s[1] for s in PIPELINE_STAGES
}


# ── 页面渲染 ──

def render_workspace_page():
    """工作台首页 — 待办任务 + 生产流水线 + 本周概览。"""
    page_header("dashboard", "工作台", "欢迎回来，这是你的视频生产全貌")
    data = _query_workspace()

    # ═══════════════════════════════════════════════════════════
    # Section 1 — 待办任务卡片
    # ═══════════════════════════════════════════════════════════
    st.markdown(section_header("bell", "待办事项", COLORS["error"]),
                unsafe_allow_html=True)

    pr_count = len(data["pending_review"])
    pub_count = len(data["approved"])
    topic_in_progress = data["status_counts"].get("idea", 0) + \
        data["status_counts"].get("topic_selected", 0)

    cols = st.columns(3)
    cards = [
        ("edit", str(pr_count), "等待审核",
         "视频已合成完毕，需要你确认质量", COLORS["error"]),
        ("send", str(pub_count), "等待发布",
         "审核已通过，可以安排发布日程", COLORS["info"]),
        ("lightbulb", str(topic_in_progress), "进行中选题",
         "选题正在共创或等待确认", COLORS["accent"]),
    ]
    for col, (ic, count, label, desc, accent) in zip(cols, cards):
        with col:
            st.markdown(
                task_card(ic, count, label, desc, accent),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # Section 2 — 生产流水线
    # ═══════════════════════════════════════════════════════════
    st.markdown(
        section_header("film", "生产流水线", COLORS["accent"],
                       right=f"共 {esc(str(data['total_videos']))} 个视频"),
        unsafe_allow_html=True,
    )

    in_progress = data["in_progress"]
    if not in_progress:
        empty_state("film", "暂无进行中的视频",
                    "选题确认后，视频将自动进入生产流水线")
    else:
        for video in in_progress[:8]:
            status = video["status"]
            color = STATUS_COLORS.get(status, COLORS["muted"])
            label = STAGE_LABELS.get(status, status)
            ic_name = PIPELINE_ICONS.get(status, "film")

            # 判断是用户需介入还是 AI 自主阶段
            user_stages = {"topic_selected", "pending_review", "approved"}
            if status in user_stages:
                hint = "需要你操作"
                hint_color = COLORS["primary"]
            else:
                hint = "AI 自动处理中"
                hint_color = COLORS["muted"]

            st.markdown(f"""
            <div style="background:{COLORS['card']}; border-radius:var(--yx-radius);
                padding:0.75rem 1rem; border:1px solid {COLORS['border']};
                border-left:3px solid {color}; margin-bottom:0.5rem;
                box-shadow:var(--yx-shadow);">
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <div style="display:flex; align-items:center; gap:0.6rem; flex:1;
                        min-width:0;">
                        <div style="width:32px; height:32px; border-radius:8px;
                            background:{color}12; display:flex; align-items:center;
                            justify-content:center; flex-shrink:0;">
                            {icon(ic_name, 'sm', color)}
                        </div>
                        <div style="min-width:0;">
                            <div style="font-size:0.9rem; font-weight:600;
                                color:{COLORS['fg']}; white-space:nowrap;
                                overflow:hidden; text-overflow:ellipsis;">
                                {esc(video['title'])}
                            </div>
                            <div style="font-size:0.75rem; color:{hint_color};">
                                {hint}
                            </div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:0.5rem;
                        flex-shrink:0;">
                        <span style="background:{color}18; color:{color};
                            padding:2px 8px; border-radius:6px;
                            font-size:0.75rem; font-weight:500;">{esc(label)}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # Section 3 — 本周概览
    # ═══════════════════════════════════════════════════════════
    st.markdown(section_header("calendar", "本周概览", COLORS["info"]),
                unsafe_allow_html=True)

    stats_cols = st.columns(4)
    stats = [
        ("选题", str(data["week_topics"]), COLORS["accent"], "lightbulb"),
        ("审核", str(data["week_reviewed"]), COLORS["primary"], "edit"),
        ("发布", str(data["week_published"]), COLORS["success"], "send"),
        ("总视频", str(data["total_videos"]), COLORS["info"], "film"),
    ]
    for col, (label, value, accent, ic) in zip(stats_cols, stats):
        with col:
            st.markdown(
                stat_card(label, value, accent, ic),
                unsafe_allow_html=True,
            )
