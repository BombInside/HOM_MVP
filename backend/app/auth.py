from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_session
from .models import User
from .config import get_settings

settings = get_settings()


async def get_current_user(session: AsyncSession = Depends(get_session), token: str = Depends()):
    """
    Проверяет и декодирует JWT, возвращает текущего пользователя.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id: int = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def has_role(user: User, required_role: str) -> bool:
    """
    Проверяет, есть ли у пользователя требуемая роль.
    """
    return bool(user.role and user.role.name == required_role)
