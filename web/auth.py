"""Authentication — Streamlit session auth + FastAPI JWT."""
import hmac
import streamlit as st
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from config.settings import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# ── Streamlit Auth ──

def check_auth():
    """Streamlit 登录认证. Call at top of app.py before page navigation."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("攸县有话说")
        st.markdown("请输入管理员密码登录")
        password = st.text_input("管理员密码", type="password")
        if st.button("登录"):
            if hmac.compare_digest(password, settings.admin_password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码错误")
        st.stop()


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
