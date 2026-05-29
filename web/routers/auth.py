"""Authentication API routes."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from config.settings import settings
from web.auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return JWT token."""
    if form_data.password != settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(username=form_data.username or "admin")
    return {"access_token": access_token, "token_type": "bearer"}
