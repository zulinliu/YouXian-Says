"""数据洞察页面 — 粉丝趋势 + TOP 视频 + AI 周报"""
import asyncio
from datetime import datetime, timedelta

import streamlit as st
from agents import OpsAgent
from web.styles import (
    COLORS, esc, icon, page_header, empty_state, stat_card,
    section_header,
)


def _load_stats() -> dict:
    """从数据库加载统计数据。"""
    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _query():
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row

                total = (await (
                    await db.execute("SELECT COUNT(*) as c FROM videos")
                ).fetchone())["c"]

                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                weekly = (await (
                    await db.execute(
                        "SELECT COUNT(*) as c FROM videos "
                        "WHERE created_at >= ?", (week_ago,))
                ).fetchone())["c"]

                pending = (await (
                    await db.execute(
                        "SELECT COUNT(*) as c FROM videos "
                        "WHERE status = 'pending_review'")
                ).fetchone())["c"]

                published = (await (
                    await db.execute(
                        "SELECT COUNT(*) as c FROM videos "
                        "WHERE status = 'published'")
                ).fetchone())["c"]

                return {
                    "total_videos": total,
                    "weekly_publishes": weekly,
                    "pending_reviews": pending,
                    "total_published": published,
                }

        return asyncio.run(_query())
    except Exception:
        return {
            "total_videos": 0, "weekly_publishes": 0,
            "pending_reviews": 0, "total_published": 0,
        }


def render_dashboard_page():
    page_header("chart", "数据洞察", "运营数据总览与趋势分析")

    stats = _load_stats()

    # ── 统计卡片网格 ──
    cols = st.columns(4)
    cards = [
        ("总视频", str(stats["total_videos"]),
         COLORS["primary"], "film"),
        ("本周新增", str(stats["weekly_publishes"]),
         COLORS["accent"], "sparkle"),
        ("已发布", str(stats["total_published"]),
         COLORS["success"], "send"),
        ("待审核", str(stats["pending_reviews"]),
         COLORS["warning"], "edit"),
    ]
    for col, (label, value, accent, ic) in zip(cols, cards):
        with col:
            st.markdown(
                stat_card(label, value, accent, ic),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:1rem;'></div>",
                unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["趋势", "周报"])

    with tab1:
        st.markdown(section_header("chart", "粉丝趋势", COLORS["accent"]),
                    unsafe_allow_html=True)
        st.caption("数据采集将在后续阶段启用")

        try:
            import altair as alt
            import pandas as pd

            source = pd.DataFrame({
                "日期": pd.date_range(end=pd.Timestamp.now(), periods=7),
                "粉丝": [0, 0, 0, 0, 0, 0, 0],
            })
            chart = (
                alt.Chart(source)
                .mark_line(color=COLORS["primary"], strokeWidth=2)
                .encode(x="日期:T", y="粉丝:Q")
                .configure_view(fill=COLORS["card"])
                .configure_axis(
                    labelColor=COLORS["muted"],
                    titleColor=COLORS["muted"],
                    gridColor=COLORS["border"],
                )
                .configure(background="transparent")
            )
            st.altair_chart(chart, use_container_width=True)
        except ImportError:
            st.line_chart({"模拟数据": [0, 0, 0, 0, 0, 0, 0]})

        st.markdown(section_header("trophy", "内容表现 TOP", COLORS["warning"]),
                    unsafe_allow_html=True)
        empty_state("trophy", "暂无发布数据",
                    "内容表现将在首次发布后 24 小时内出现")

    with tab2:
        st.markdown(section_header("book", "周度分析报告", COLORS["info"]),
                    unsafe_allow_html=True)
        if st.button("生成周报", type="primary", use_container_width=True):
            with st.spinner("正在生成周报..."):
                agent = OpsAgent()
                report = asyncio.run(agent.generate_weekly_report())
                if report:
                    report_text = report if isinstance(report, str) else str(report)
                    st.markdown(f"""
                    <div style="background:{COLORS['card']};
                        border-radius:var(--yx-radius); padding:1.25rem;
                        border:1px solid {COLORS['border']};">
                        <div style="font-size:0.875rem; color:{COLORS['fg']};
                            white-space:pre-wrap;">
                            {esc(report_text)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("暂无足够数据生成周报")

        st.caption("周报将在数据积累后自动生成。")
