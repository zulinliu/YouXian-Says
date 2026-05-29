"""Authentication — Streamlit session auth + FastAPI JWT."""
import hmac
import logging

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from config.settings import settings
from web.styles import render_logo, COLORS

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
_COOKIE_NAME = "yx_token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# ── Streamlit Auth ──

def _restore_from_cookie():
    """从浏览器 cookie 恢复认证状态（解决刷新/导航丢失 session）。"""
    try:
        token = st.context.cookies.get(_COOKIE_NAME)
        if not token:
            return
        payload = jwt.decode(token, _jwt_secret(), algorithms=[ALGORITHM])
        if payload.get("sub") == "admin":
            st.session_state.authenticated = True
    except Exception:
        logger.debug("cookie 认证恢复失败", exc_info=True)


def _set_auth_cookie():
    """通过同源 iframe 内的 JavaScript 设置认证 cookie。"""
    token = create_access_token()
    max_age = ACCESS_TOKEN_EXPIRE_HOURS * 3600
    components.html(
        f'<script>document.cookie="{_COOKIE_NAME}={token}; '
        f'path=/; max-age={max_age}; SameSite=Lax";</script>',
        height=0,
    )


def check_auth():
    """Streamlit 登录认证. Call at top of app.py before page navigation."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # 从 cookie 恢复认证状态（处理刷新/导航丢失 session_state）
    if not st.session_state.authenticated:
        _restore_from_cookie()

    if not st.session_state.authenticated:
        # ── 登录页 ──
        st.markdown(f"""<style>
        /* 隐藏侧边栏（高特异性覆盖全局显示规则） */
        html body section[data-testid="stSidebar"] {{ display: none !important; }}
        html body [data-testid="stSidebarNav"] {{ display: none !important; }}
        /* 透明 header */
        [data-testid="stHeader"] {{ background: transparent !important; }}
        /* 登录页渐变背景 */
        .stApp {{
            background: linear-gradient(160deg, {COLORS['bg']} 0%, {COLORS['bg_deep']} 60%, #E8E4DF 100%) !important;
        }}
        /* 登录卡片 */
        .stForm {{
            border: none !important;
            border-radius: 20px !important;
            padding: 2.5rem 2rem !important;
            background: {COLORS['card']} !important;
            box-shadow: 0 8px 40px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.04) !important;
            animation: yxLoginIn 0.4s ease-out;
        }}
        @keyframes yxLoginIn {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        /* 密码输入框 */
        .stForm .stTextInput input {{
            min-height: 50px !important;
            font-size: 15px !important;
            padding: 0 1.125rem !important;
            border-radius: 12px !important;
            border: 1.5px solid {COLORS['border']} !important;
            background: {COLORS['bg']} !important;
            color: {COLORS['fg']} !important;
            letter-spacing: 0.05em;
            transition: all 0.2s ease !important;
        }}
        .stForm .stTextInput input:focus {{
            border-color: {COLORS['primary']} !important;
            box-shadow: 0 0 0 3px {COLORS['primary']}1A !important;
            background: {COLORS['card']} !important;
        }}
        .stForm .stTextInput input::placeholder {{
            color: {COLORS['muted_light']} !important;
            letter-spacing: 0;
        }}
        /* 登录按钮 */
        .stForm .stFormSubmitButton > button {{
            min-height: 48px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            background: {COLORS['primary']} !important;
            border: none !important;
            color: white !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 8px {COLORS['primary']}33 !important;
        }}
        .stForm .stFormSubmitButton > button:hover {{
            background: {COLORS['primary_dark']} !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 16px {COLORS['primary']}44 !important;
        }}
        </style>""", unsafe_allow_html=True)

        logo = render_logo(72)
        st.markdown(f"""
        <div style="text-align:center; padding:6rem 0 2.5rem;">
            {logo}
            <div style="font-size:1.75rem; font-weight:700; color:{COLORS['fg']};
                margin-top:1.5rem; letter-spacing:0.02em; line-height:1.3;">
                攸县有话说
            </div>
            <div style="font-size:0.9rem; color:{COLORS['muted']};
                margin-top:0.5rem; font-weight:400;">
                AI 方言短视频生产平台
            </div>
        </div>
        """, unsafe_allow_html=True)

        _, center, _ = st.columns([2, 1, 2])
        with center:
            with st.form("login_form", clear_on_submit=False):
                password = st.text_input(
                    "管理员密码", type="password",
                    label_visibility="collapsed",
                    placeholder="请输入管理员密码",
                )
                submitted = st.form_submit_button(
                    "登录", type="primary", use_container_width=True,
                )
            if submitted:
                if hmac.compare_digest(password, settings.admin_password):
                    st.session_state.authenticated = True
                    st.session_state._set_cookie = True
                    st.rerun()
                else:
                    st.error("密码错误")
            st.markdown(f"""
            <div style='text-align:center; margin-top:1.25rem;'>
                <span style='font-size:0.8rem; color:{COLORS['muted_light']}; font-weight:400;'>
                    一句攸县话，讲活一座城</span>
            </div>
            """, unsafe_allow_html=True)
        st.stop()
    else:
        # 已认证 — 设置 cookie（仅登录后首次渲染触发）
        if st.session_state.pop("_set_cookie", False):
            _set_auth_cookie()

        # 确保侧边栏可见（覆盖可能的残留 display:none CSS）
        st.markdown("""<style>
        section[data-testid="stSidebar"] { display: flex !important; }
        </style>""", unsafe_allow_html=True)


# ── FastAPI JWT Auth ──

def _jwt_secret() -> str:
    """获取 JWT 签名密钥（独立于 admin 密码）"""
    return settings.jwt_secret_key


async def verify_token(token: str = Depends(oauth2_scheme)):
    """Dependency: verify JWT token, return username from 'sub' claim."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证令牌",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except InvalidTokenError:
        raise credentials_exception


def create_access_token(username: str = "admin") -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, _jwt_secret(), algorithm=ALGORITHM)
