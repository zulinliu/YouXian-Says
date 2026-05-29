"""数据看板页面 — 粉丝趋势 + TOP视频 + 周报"""
import streamlit as st
from agents import OpsAgent


def render_dashboard_page():
    st.title("数据看板")

    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总视频数", "0", delta=None)
    with col2:
        st.metric("本周发布", "0", delta=None)
    with col3:
        st.metric("总粉丝", "--", delta=None)
    with col4:
        st.metric("待审核", "0")

    st.markdown("---")

    tab1, tab2 = st.tabs(["📈 趋势", "📊 周报"])

    with tab1:
        st.subheader("粉丝趋势")
        st.caption("数据采集将在后续阶段启用")
        st.line_chart({"模拟数据": [0, 0, 0, 0, 0, 0, 0]})

        st.subheader("内容表现 TOP")
        st.info("暂无发布数据，内容表现将在发布后自动统计。")

    with tab2:
        st.subheader("周度分析报告")
        if st.button("生成周报"):
            with st.spinner("正在生成周报..."):
                import asyncio
                agent = OpsAgent()
                report = asyncio.run(agent.generate_weekly_report())
                if report:
                    st.json(report)
                else:
                    st.warning("暂无足够数据生成周报")

        st.caption("周报将在数据积累后自动生成。")
