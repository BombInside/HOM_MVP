# -*- coding: utf-8 -*-
"""
Роуты для админ-панели (bootstrap создания первого администратора).
Добавлен GET /adminpanel/bootstrap (алиас для проверки статуса),
чтобы избежать 405 при запросах со старого фронтенда.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field

from app.db import get_session
from app.models import User, Role, UserRoleLink


router = APIRouter(prefix="/adminpanel", tags=["AdminPanel"])


# ==========================
# 📦 Модель входных данных
# ==========================
class AdminBootstrapIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(None, min_length=2, max_length=128)


# ==========================
# 📊 GET /bootstrap/status — проверка инициализации
# ==========================
@router.get("/bootstrap/status", response_model=dict)
async def bootstrap_status(db: AsyncSession = Depends(get_session)) -> dict:
    """Проверяет, создан ли хотя бы один пользователь (инициализация выполнена)."""
    admin_exists = await db.scalar(select(User.id).limit(1))
    return {"admin_exists": admin_exists is not None}


# ==========================
# 🔁 GET /bootstrap (алиас для старого фронта)
# ==========================
@router.get("/bootstrap", response_model=dict)
async def bootstrap_status_alias(db: AsyncSession = Depends(get_session)) -> dict:
    """Совместимый алиас под старый фронтенд (возвращает тот же результат)."""
    return await bootstrap_status(db)


# ==========================
# 🚀 POST /bootstrap — инициализация системы
# ==========================
@router.post("/bootstrap", status_code=status.HTTP_201_CREATED, response_model=dict)
async def bootstrap_create_admin(data: AdminBootstrapIn, db: AsyncSession = Depends(get_session)) -> dict:
    """
    Одноразовое создание первого администратора и роли Admin.
    Если уже существует пользователь, возвращает 409.
    """
    # Проверяем, инициализирована ли система
    exists = await db.scalar(select(User.id).limit(1))
    if exists is not None:
        raise HTTPException(status_code=409, detail="Already initialized")

    # Создаём или находим роль Admin
    role_admin = (await db.execute(select(Role).where(Role.name == "Admin"))).scalar_one_or_none()
    if role_admin is None:
        role_admin = Role(name="Admin", description="Full access")
        db.add(role_admin)
        await db.flush()

    # Создаём администратора
    user = User(email=data.email)
    user.set_password(data.password)
    user.is_admin = True
    user.is_active = True

    db.add(user)
    await db.flush()

    # Привязываем роль
    db.add(UserRoleLink(user_id=user.id, role_id=role_admin.id))
    await db.commit()

    return {
        "message": "Admin user created",
        "user_id": user.id,
        "role_id": role_admin.id,
    }
