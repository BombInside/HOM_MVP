# -*- coding: utf-8 -*-
"""
Маршруты аутентификации (login / me) + зависимость current_user.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from .config import get_settings
from .db import get_session
from .models import User, Role, UserRoleLink
from .security import verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()
security_scheme = HTTPBearer(auto_error=False)


def _create_access_token(sub: str) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MIN)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Проверяет JWT и возвращает текущего пользователя или выбрасывает 401."""
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await session.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.post("/login")
async def login(payload: Dict[str, str], session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    """Логин: проверяет email+пароль и возвращает access_token."""
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user = await session.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    result = await session.execute(
        select(Role.name)
        .join(UserRoleLink, UserRoleLink.role_id == Role.id)
        .where(UserRoleLink.user_id == user.id)
    )
    roles: List[str] = [r[0] for r in result.all()]

    token = _create_access_token(sub=email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"email": user.email, "roles": roles, "is_admin": getattr(user, "is_admin", False)},
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    """Возвращает сведения о текущем пользователе (по токену)."""
    result = await session.execute(
        select(Role.name)
        .join(UserRoleLink, UserRoleLink.role_id == Role.id)
        .where(UserRoleLink.user_id == current_user.id)
    )
    roles: List[str] = [r[0] for r in result.all()]
    return {
        "email": current_user.email,
        "roles": roles,
        "is_admin": getattr(current_user, "is_admin", False),
    }
