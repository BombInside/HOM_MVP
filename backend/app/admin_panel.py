# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field

from .db import get_session
from .models import User, Role, UserRoleLink
from .security import hash_password

router = APIRouter(prefix="/adminpanel", tags=["adminpanel"])


class BootstrapRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)


class BootstrapResponse(BaseModel):
    ok: bool
    created_user_id: int | None = None
    message: str | None = None
    admin_exists: bool


async def _admin_exists(session):
    """Проверяет, существует ли пользователь с ролью 'admin'."""
    q = (
        select(User)
        .join(UserRoleLink, UserRoleLink.user_id == User.id)
        .join(Role, Role.id == UserRoleLink.role_id)
        .where(Role.name == "admin")
    )
    return await session.scalar(q)


@router.get("/bootstrap", response_model=BootstrapResponse)
async def admin_bootstrap_state(session: AsyncSession = Depends(get_session)):
    exists = await _admin_exists(session)
    return BootstrapResponse(ok=True, admin_exists=exists)


@router.post("/bootstrap", response_model=BootstrapResponse)
async def admin_bootstrap_post(payload: BootstrapRequest, session: AsyncSession = Depends(get_session)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    # Ensure roles exist
    q = await session.execute(select(Role).where(Role.name == "admin"))
    admin_role = q.scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name="admin", description="Администратор")
        session.add(admin_role)
        await session.flush()

    # Create user if not exists
    q = await session.execute(select(User).where(User.email == payload.email))
    existing = q.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")

    user = User(email=str(payload.email), password_hash=hash_password(payload.password), is_active=True)
    session.add(user)
    await session.flush()

    # Link role
    await session.execute(UserRoleLink.insert().values(user_id=user.id, role_id=admin_role.id))
    await session.commit()

    return BootstrapResponse(ok=True, admin_exists=True, created_user_id=user.id, message="Администратор создан")
