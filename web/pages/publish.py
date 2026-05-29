"""发布管理页面 — 待确认队列 + 平台选择 + 确认优先"""
import streamlit as st


def render_publish_page():
    st.title("发布管理")
    st.markdown("管理待发布视频 — 所有发布默认进入确认队列。")

    # Two-step publish flow: Step 1 = queue, Step 2 = confirm
    tab1, tab2 = st.tabs(["📋 待发布队列", "✅ 已发布"])

    with tab1:
        st.info("暂无待发布视频。完成审核后，视频将出现在这里。")

        # Demo with mock data
        demo_video = st.session_state.get("confirmed_topic")
        if demo_video:
            st.markdown("---")
            st.markdown(f"### 待发布: {demo_video.get('title', '示例视频')}")

            with st.form("publish_form"):
                platforms = st.multiselect(
                    "选择发布平台",
                    ["抖音", "视频号"],
                    default=["抖音", "视频号"],
                    help="MVP 阶段支持抖音和视频号"
                )
                schedule_type = st.radio("发布时间", ["立即发布", "定时发布"], horizontal=True)
                scheduled_time = None
                if schedule_type == "定时发布":
                    from datetime import datetime, timedelta
                    scheduled_time = st.date_input("日期")

                st.markdown("---")
                st.markdown("**发布确认** — 请确认以下信息：")

                review_title = st.text_input("视频标题", value=demo_video.get("title", ""))
                review_tags = st.text_input("标签（逗号分隔）", value="攸县话,方言")
                review_desc = st.text_area("描述")

                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("✅ 确认发布", type="primary")
                with col2:
                    st.form_submit_button("取消")

                if submitted:
                    st.toast(f"已添加到发布队列: {review_title}")
                    st.success(f"发布任务已提交: {', '.join(platforms)}")

    with tab2:
        st.info("暂无已发布的视频。")
