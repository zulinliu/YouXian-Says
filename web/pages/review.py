"""视频审核页面 — 分镜预览 + 视频播放 + 结构化审核 + 状态机校验"""
import asyncio
import json
import logging
from datetime import datetime

import streamlit as st
from web.models import VALID_TRANSITIONS
from web.styles import (
    COLORS, STATUS_COLORS, esc, icon, page_header, empty_state,
    pipeline_progress, badge,
)

logger = logging.getLogger(__name__)


def _validate_transition(current: str, target: str) -> bool:
    """校验状态转换是否合法。"""
    allowed = VALID_TRANSITIONS.get(current, [])
    return target in allowed


def _load_pending_videos() -> list[dict]:
    """从数据库加载待审核视频。"""
    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _query():
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT id, title, status, created_at, updated_at "
                    "FROM videos WHERE status = 'pending_review' "
                    "ORDER BY created_at DESC"
                )
                return [dict(row) for row in await cursor.fetchall()]

        return asyncio.run(_query())
    except Exception:
        logger.exception("加载待审核视频失败")
        return []


def _load_reviewed_videos() -> list[dict]:
    """从数据库加载已审核视频。"""
    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _query():
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT id, title, status, created_at, updated_at, "
                    "CASE WHEN dialect_dictionary IS NOT NULL "
                    "THEN dialect_dictionary ELSE '' END as review_notes "
                    "FROM videos WHERE status IN ('approved', 'rejected') "
                    "ORDER BY updated_at DESC LIMIT 20"
                )
                return [dict(row) for row in await cursor.fetchall()]

        return asyncio.run(_query())
    except Exception:
        logger.exception("加载已审核视频失败")
        return []


def _submit_review(video_id: int, current_status: str,
                   new_status: str, review_data: dict) -> bool:
    """提交审核 — 校验状态机 + 原子更新状态 + 存储审核反馈。"""
    if not _validate_transition(current_status, new_status):
        return False

    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _update():
            async with aiosqlite.connect(DB_PATH) as db:
                cur = await db.execute(
                    "UPDATE videos SET status = ?, dialect_dictionary = ? "
                    "WHERE id = ? AND status = ?",
                    (new_status, json.dumps(review_data, ensure_ascii=False),
                     video_id, current_status),
                )
                await db.commit()
                return cur.rowcount == 1

        return asyncio.run(_update())
    except Exception:
        logger.exception("提交审核失败")
        return False


def render_review_page():
    page_header("edit", "视频审核", "查看和审核视频，提供结构化修改意见")

    tab1, tab2 = st.tabs(["待审核", "已审核"])

    with tab1:
        pending = _load_pending_videos()

        if not pending:
            empty_state("film", "暂无待审核视频",
                        "视频合成完成后将自动出现在这里")
        else:
            video = pending[0]

            pipeline_progress(video["status"])
            col_video, col_form = st.columns([3, 2])

            with col_video:
                video_path = f"output/final/{video['id']}.mp4"
                try:
                    st.video(video_path)
                except Exception:
                    st.markdown(f"""
                    <div style="background:{COLORS['card']}; border-radius:var(--yx-radius);
                        aspect-ratio:16/9; display:flex; align-items:center;
                        justify-content:center; border:1px solid {COLORS['border']};">
                        <div style="text-align:center; color:{COLORS['muted']};">
                            <div style="margin-bottom:0.25rem;">{icon('film', 'xl', COLORS['muted_light'])}</div>
                            <div>视频加载中</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="display:flex; gap:0.5rem; margin-top:0.5rem;
                    flex-wrap:wrap; align-items:center;">
                    {badge(video['status'], STATUS_COLORS.get(video['status'], COLORS['muted']))}
                    {badge('攸县方言', COLORS['accent'])}
                    <span style="color:{COLORS['muted']}; font-size:0.75rem;
                        margin-left:auto;">
                        {esc(video['title'])}
                    </span>
                </div>
                """, unsafe_allow_html=True)

            with col_form:
                with st.form("review_form"):
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:0.4rem;
                        margin-bottom:0.5rem;">
                        {icon('edit', 'sm', COLORS['primary'])}
                        <span style="font-weight:600; color:{COLORS['fg']};">
                            审核意见</span>
                    </div>
                    """, unsafe_allow_html=True)
                    action = st.radio("审核结果",
                                      ["通过", "轻微修改", "重新制作"],
                                      horizontal=True)

                    dimensions = []
                    comment = ""
                    if action != "通过":
                        dimensions = st.multiselect(
                            "修改维度",
                            ["画面/B-roll", "配音/语气", "字幕/翻译",
                             "背景音乐", "脚本内容"],
                        )
                        comment = st.text_area("具体修改要求")

                    if st.form_submit_button("提交审核",
                                             type="primary",
                                             use_container_width=True):
                        if action == "通过":
                            new_status = "approved"
                        else:
                            new_status = "rejected"

                        review_data = {
                            "action": action,
                            "dimensions": dimensions,
                            "comment": comment,
                            "reviewed_at": str(datetime.now()),
                        }

                        ok = _submit_review(
                            video["id"], video["status"],
                            new_status, review_data,
                        )
                        if ok:
                            st.toast(f"审核完成: {action}",
                                     icon=":material/check_circle:")
                            st.rerun()
                        else:
                            st.error("状态转换不合法，请刷新后重试")

            if len(pending) > 1:
                with st.expander(f"还有 {len(pending) - 1} 个视频待审核"):
                    for v in pending[1:]:
                        c = STATUS_COLORS.get(v["status"], COLORS["muted"])
                        st.markdown(f"""
                        <div style="display:flex; align-items:center; gap:0.5rem;
                            padding:0.5rem 0; border-bottom:1px solid {COLORS['border']};">
                            {badge(v['status'], c)}
                            <span style="color:{COLORS['fg']}; font-size:0.9rem;">
                                {esc(v['title'])}</span>
                        </div>
                        """, unsafe_allow_html=True)

    with tab2:
        reviewed = _load_reviewed_videos()
        if not reviewed:
            empty_state("check", "暂无已审核视频",
                        "审核通过的视频将在此处归档")
        else:
            for v in reviewed:
                color = STATUS_COLORS.get(v["status"], COLORS["muted"])
                with st.expander(f"{v['title']}", expanded=False):
                    st.markdown(f"""
                    <div style="display:flex; gap:0.5rem; align-items:center;
                        margin-bottom:0.5rem;">
                        {badge(v['status'], color)}
                    </div>
                    <div style="font-size:0.8rem; color:{COLORS['muted']};">
                        创建: {esc(str(v['created_at']))} |
                        更新: {esc(str(v['updated_at']))}
                    </div>
                    """, unsafe_allow_html=True)
                    # 显示审核反馈
                    notes = v.get("review_notes", "")
                    if notes:
                        try:
                            data = json.loads(notes)
                            if data.get("comment"):
                                st.markdown(f"""
                                <div style="background:{COLORS['bg_deep']};
                                    border-radius:8px; padding:0.75rem;
                                    margin-top:0.5rem; font-size:0.85rem;
                                    color:{COLORS['fg_light']};">
                                    {esc(data['comment'])}
                                </div>
                                """, unsafe_allow_html=True)
                            if data.get("dimensions"):
                                st.markdown(
                                    "修改维度: " + ", ".join(data["dimensions"])
                                )
                        except (json.JSONDecodeError, TypeError):
                            pass
