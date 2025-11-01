# -*- coding: utf-8 -*-
"""
Роуты для админ-панели (bootstrap создания первого администратора).
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field

from app.db import get_session
from app.models import User, Role, UserRoleLink
from app.security import hash_password

router = APIRouter(prefix="/adminpanel", tags=["AdminPanel"])


# ---------- СХЕМЫ ----------
class BootstrapRequest(BaseModel):
    """Входные данные для создания первого администратора."""
    email: EmailStr
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)


class BootstrapResponse(BaseModel):
    """Ответ API для bootstrap-эндпоинтов."""
    ok: bool
    admin_exists: bool
    created_user_id: int | None = None
    message: str | None = None


# ---------- СЛУЖЕБНЫЕ ФУНКЦИИ ----------
async def _admin_exists(session: AsyncSession) -> bool:
    """
    Проверяет, существует ли пользователь с ролью 'admin'.
    Возвращает True/False.
    """
    q = (
        select(User)
        .join(UserRoleLink, UserRoleLink.user_id == User.id)
        .join(Role, Role.id == UserRoleLink.role_id)
        .where(Role.name == "admin")
    )
    user = await session.scalar(q)
    return user is not None


# ---------- ЭНДПОИНТЫ ----------

@router.get("/bootstrap", response_model=BootstrapResponse)
async def admin_bootstrap_state(session: AsyncSession = Depends(get_session)) -> BootstrapResponse:
    """
    ✅ Публичный эндпоинт: проверяет, создан ли администратор.
    Не требует авторизации, чтобы можно было создать первого пользователя.
    """
    exists = await _admin_exists(session)
    return BootstrapResponse(ok=True, admin_exists=exists)


@router.post("/bootstrap", response_model=BootstrapResponse)
async def admin_bootstrap_post(
    payload: BootstrapRequest,
    session: AsyncSession = Depends(get_session),
) -> BootstrapResponse:
    """
    Создаёт первого администратора, если он ещё не существует.
    Проверяет пароли, наличие роли 'admin', и добавляет связь.
    """

    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    if await _admin_exists(session):
        raise HTTPException(status_code=400, detail="Administrator already exists")

    q = await session.execute(select(Role).where(Role.name == "admin"))
    admin_role = q.scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name="admin", description="Administrator")
        session.add(admin_role)
        await session.flush()

    q = await session.execute(select(User).where(User.email == payload.email))
    existing = q.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    user = User(
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        is_active=True,
        is_admin=True,
    )
    session.add(user)
    await session.flush()

    link = UserRoleLink(user_id=user.id, role_id=admin_role.id)
    session.add(link)

    await session.commit()

    return BootstrapResponse(
        ok=True,
        admin_exists=True,
        created_user_id=user.id,
        message="Admin user created successfully.",
    )
