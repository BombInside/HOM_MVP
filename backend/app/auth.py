from __future__ import annotations

from typing import Any, Optional, cast
from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import get_session
from .models import User

ALGORITHM = "HS256"


def hash_password(raw: str) -> str:
    """Возвращает SHA256-хэш пароля."""
    import hashlib

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_password(raw: str, hashed: str) -> bool:
    """Сравнивает исходный и хэшированный пароли."""
    return hash_password(raw) == hashed


def create_access_token(payload: dict[str, Any], expires_delta: Optional[int] = None) -> str:
    """Создает JWT-токен с опциональным временем жизни."""
    to_encode = payload.copy()
    expire_minutes = float(expires_delta or getattr(settings, "JWT_EXPIRE_MIN", 60))
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def has_role(user: User, role_name: str) -> bool:
    """Проверяет, имеет ли пользователь указанную роль."""
    roles = getattr(user, "roles", []) or []
    return any(getattr(r, "name", None) == role_name for r in roles)


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Возвращает текущего аутентифицированного пользователя по JWT."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    # mypy-safe SQLAlchemy select
    stmt = cast(Any, select(User).where(User.id == int(user_id)))  # fixed type-safety
    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=stat_
