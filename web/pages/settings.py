"""系统设置页面 — 查看/切换/编辑模型参数"""
import os
import time

import streamlit as st
from config.model_registry import ModelRegistry
from web.styles import COLORS, esc, page_header


def test_api_connection(api_base: str, model_name: str, api_key: str,
                         env_key: str, provider: str) -> dict:
    """Test API connectivity by making a lightweight request."""
    effective_key = api_key or os.environ.get(env_key, "")

    if effective_key and effective_key != "sk-xxx":
        try:
            import httpx
            start = time.monotonic()

            if provider in ("deepseek", "openai", "openai_relay", "zhipu_relay"):
                resp = httpx.get(
                    f"{api_base.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {effective_key}"},
                    timeout=10,
                )
            else:
                resp = httpx.get(api_base.rstrip('/'), timeout=10)

            latency = int((time.monotonic() - start) * 1000)

            if 200 <= resp.status_code < 300:
                return {"ok": True, "latency_ms": latency, "error": ""}
            return {
                "ok": False, "latency_ms": latency,
                "error": f"HTTP {resp.status_code}: {resp.text[:100]}",
            }

        except Exception as e:
            return {"ok": False, "latency_ms": 0, "error": str(e)[:100]}

    if not api_base.startswith("https://"):
        return {
            "ok": False, "latency_ms": 0,
            "error": "API地址必须以 https:// 开头",
        }

    return {
        "ok": True, "latency_ms": 0,
        "error": "连接测试仅验证URL格式（未配置API Key）",
    }


def _model_card_html(model: dict, tier_color: str = "#78716C"):
    name = model["name"]
    provider = model.get("provider", "")
    cost = model.get("cost_per_m_tokens", 0)
    ctx = model.get("max_context", "N/A")
    notes = model.get("notes", "")

    notes_html = (
        f'<div style="font-size:0.75rem; color:{COLORS["muted"]}; '
        f'margin-top:0.15rem;">{esc(notes)}</div>'
        if notes else ""
    )
    return f"""
    <div style="background:{COLORS['card']}; border-radius:var(--yx-radius-sm);
        padding:0.75rem 1rem; margin-bottom:0.5rem;
        border-left:3px solid {tier_color};">
        <div style="font-size:0.95rem; font-weight:600;
            color:{COLORS['fg']};">{esc(name)}</div>
        <div style="display:flex; gap:0.5rem; margin-top:0.15rem; flex-wrap:wrap;">
            <span style="font-size:0.75rem; color:{COLORS['muted']};">
                {esc(provider)}</span>
            <span style="font-size:0.75rem; color:{COLORS['border_hover']};">
                |</span>
            <span style="font-size:0.75rem; color:{COLORS['muted']};">
                {cost}元/百万token</span>
            <span style="font-size:0.75rem; color:{COLORS['border_hover']};">
                |</span>
            <span style="font-size:0.75rem; color:{COLORS['muted']};">
                上下文: {esc(str(ctx))}</span>
        </div>
        {notes_html}
    </div>
    """


def render_settings_page():
    page_header("settings", "系统设置", "配置各功能维度的模型参数与 API 密钥")

    registry = ModelRegistry.list_all()

    for fid, func_info in registry.items():
        active_id = func_info["active_id"]
        active_name = func_info["active_name"]
        function_name = func_info["function_name"]

        with st.expander(f"**{function_name}** — 当前: {active_name}",
                         expanded=False):
            st.markdown(f"""
            <div style="display:flex; align-items:center;
                justify-content:space-between; margin-bottom:0.5rem;">
                <span style="font-size:0.9rem; color:{COLORS['fg']};">
                    当前使用: <strong>{esc(active_name)}</strong>
                    <code style="font-size:0.8rem; color:{COLORS['muted']};">
                        ({esc(active_id)})</code>
                </span>
                <span style="background:{COLORS['primary']}; color:white;
                    padding:3px 10px; border-radius:10px; font-size:0.75rem;
                    font-weight:500;">当前使用</span>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            for model in func_info["options"]:
                model_id = model["id"]
                is_active = model_id == active_id
                tier_color = COLORS["primary"] if is_active else COLORS["warning"]

                st.markdown(
                    _model_card_html(model, tier_color),
                    unsafe_allow_html=True,
                )

                with st.form(key=f"form_{fid}_{model_id}",
                             clear_on_submit=False):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        api_base = st.text_input(
                            "API 地址",
                            value=model.get("api_base", ""),
                            key=f"api_base_{fid}_{model_id}",
                            placeholder="https://api.example.com",
                        )
                    with c2:
                        model_name = st.text_input(
                            "模型名称",
                            value=model.get("model_name", ""),
                            key=f"model_name_{fid}_{model_id}",
                            placeholder="model-name",
                        )
                    with c3:
                        api_key = st.text_input(
                            "API Key",
                            type="password",
                            placeholder=model.get(
                                "api_key_masked", "输入 API Key"),
                            key=f"api_key_{fid}_{model_id}",
                        )

                    col1, col2 = st.columns(2)
                    with col1:
                        save_clicked = st.form_submit_button(
                            "保存参数", use_container_width=True)
                    with col2:
                        switch_clicked = st.form_submit_button(
                            "切换", use_container_width=True,
                            disabled=is_active)

                    if save_clicked:
                        try:
                            ModelRegistry.update_model_config(
                                function_id=fid,
                                model_id=model_id,
                                api_base=api_base or None,
                                api_key=api_key or None,
                                model_name=model_name or None,
                            )
                            st.toast(f"{model['name']} 参数已保存",
                                     icon=":material/check_circle:")
                        except Exception as e:
                            st.toast(f"保存失败: {e}",
                                     icon=":material/error:")

                    if switch_clicked:
                        try:
                            ModelRegistry.switch(
                                function_id=fid, model_id=model_id)
                            st.toast(f"已切换到 {model['name']}",
                                     icon=":material/check_circle:")
                        except Exception as e:
                            st.toast(f"切换失败: {e}",
                                     icon=":material/error:")

                test_key = f"test_{fid}_{model_id}"
                if st.button("测试连接", key=test_key):
                    current_base = st.session_state.get(
                        f"api_base_{fid}_{model_id}",
                        model.get("api_base", ""))
                    current_key = st.session_state.get(
                        f"api_key_{fid}_{model_id}", "")
                    result = test_api_connection(
                        api_base=current_base,
                        model_name=model.get("model_name", ""),
                        api_key=current_key,
                        env_key=model.get("api_key_env", ""),
                        provider=model.get("provider", ""),
                    )
                    if result["ok"]:
                        msg = (f"连接正常"
                               f"{(' - ' + result['error']) if result['error'] else ''}")
                        st.toast(msg, icon=":material/check_circle:")
                    else:
                        st.toast(f"{result['error']}",
                                 icon=":material/error:")

                st.divider()
