# -*- coding: utf-8 -*-
"""
JWT-аутентификация и зависимости FastAPI.
"""
from __future__ import annotations
from typing import Optional, Annotated
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_session
from .models import User
from .security import verify_password

settings = get_settings()
# Используем auto_error=False, чтобы middleware мог перехватить ошибку 401, если нужно
bearer = HTTPBearer(auto_error=False) 


def create_access_token(sub: str, expires_minutes: Optional[int] = None) -> str:
    """
    Создаёт JWT access-токен.
    :param sub: subject (обычно user_id или email)
    :param expires_minutes: срок жизни, мин.
    """
    now = datetime.now(tz=timezone.utc)
    exp_delta = timedelta(minutes=expires_minutes or settings.JWT_EXPIRE_MIN)
    payload = {"sub": sub, "iat": int(now.timestamp()), "exp": int((now + exp_delta).timestamp())}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def authenticate_user(session: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Валидирует пользователя по email/паролю.
    """
    q = await session.execute(select(User).where(User.email == email))
    user = q.scalars().first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Достает текущего пользователя из JWT Authorization: Bearer ... .
    """
    if creds is None or not creds.scheme.lower() == "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        # sub может быть email или id, в этом шаблоне — email
        q = await session.execute(select(User).where(User.email == sub))
        user = q.scalars().first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not active")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def admin_required(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Dependency для проверки прав администратора."""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires administrator privileges",
        )
    return current_user