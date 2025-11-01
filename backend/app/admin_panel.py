# -*- coding: utf-8 -*-
"""
Маршруты админ-панели:
- Одноразовый bootstrap для создания первого администратора
- CRUD для ролей и прав
Возвращает только JSON, без HTML-страниц.
"""

from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from .config import get_settings
from .db import get_session
from .models import User, Role, Permission, RolePermissionLink, UserRoleLink
from .security import hash_password
from .auth import get_current_user

router = APIRouter(tags=["admin-panel"])
settings = get_settings()


async def _admin_exists(session: AsyncSession) -> bool:
    """Проверяет, существует ли хотя бы один пользователь с ролью admin."""
    q = await session.execute(select(Role).where(Role.name == "admin"))
    admin_role = q.scalars().first()
    if not admin_role:
        return False
    q2 = await session.execute(select(UserRoleLink).where(UserRoleLink.role_id == admin_role.id))
    return q2.first() is not None


@router.get("/health", include_in_schema=False)
async def health() -> dict:
    """Healthcheck для контейнера/nginx."""
    return {"status": "ok"}


# ================= BOOTSTRAP ADMIN =================

@router.get("/adminpanel/bootstrap/status", response_class=JSONResponse)
async def admin_bootstrap_status(session: AsyncSession = Depends(get_session)):
    """Возвращает состояние: создан ли уже администратор."""
    exists = await _admin_exists(session)
    return {"admin_exists": exists}


class BootstrapPayload(BaseModel):
    email: str
    password: str


@router.post("/adminpanel/bootstrap", response_class=JSONResponse)
async def admin_bootstrap_post(payload: BootstrapPayload, session: AsyncSession = Depends(get_session)):
    """
    Создаёт первого администратора в системе.
    Если админ уже есть — возвращает сообщение и код 400.
    """
    if await _admin_exists(session):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Администратор уже существует."},
        )

    email = payload.email.strip().lower()
    password = payload.password.strip()
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email и пароль обязательны")

    # создаём роль admin, если нет
    q = await session.execute(select(Role).where(Role.name == "admin"))
    admin_role = q.scalars().first()
    if not admin_role:
        admin_role = Role(name="admin", description="Полные права")
        session.add(admin_role)
        await session.flush()

    # создаём пользователя
    user = User(email=email, password_hash=hash_password(password), is_active=True)
    session.add(user)
    await session.flush()

    # линкуем роль
    link = UserRoleLink(user_id=user.id, role_id=admin_role.id)  # type: ignore[arg-type]
    session.add(link)
    await session.commit()

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "Администратор успешно создан."
        },
    )


# ================= ROLE MANAGEMENT =================

def _require_admin(user: User) -> None:
    """Проверяем, что у пользователя есть роль admin."""
    if not any(r.name == "admin" for r in user.roles):
        raise HTTPException(status_code=403, detail="Admin role required")


@router.get("/adminpanel/roles", response_class=JSONResponse)
async def list_roles(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Возвращает список ролей и их прав."""
    _require_admin(user)
    q = await session.execute(select(Role))
    roles = q.scalars().all()
    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": [p.code for p in role.permissions],
        }
        for role in roles
    ]


class RoleUpsertPayload(BaseModel):
    """Тело запроса для создания или обновления роли."""
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


@router.post("/adminpanel/roles", response_class=JSONResponse)
async def create_role(
    payload: RoleUpsertPayload,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Создаёт новую роль и назначает права."""
    _require_admin(user)
    name = payload.name.strip()
    if not name:
        raise HTTPException(400, "Поле name обязательно")

    role = Role(name=name, description=payload.description)
    session.add(role)
    await session.flush()

    codes = [c.strip() for c in payload.permissions if c.strip()]
    if codes:
        q = await session.execute(select(Permission).where(Permission.code.in_(codes)))
        existing = {p.code: p for p in q.scalars().all()}
        new_perms = []
        for code in codes:
            perm = existing.get(code) or Permission(code=code)
            if not perm.id:
                session.add(perm)
                await session.flush()
            new_perms.append(perm)
        role.permissions = new_perms  # type: ignore[assignment]

    await session.commit()
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "permissions": [p.code for p in role.permissions],
    }


@router.put("/adminpanel/roles/{role_id}", response_class=JSONResponse)
async def update_role(
    role_id: int,
    payload: RoleUpsertPayload,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Обновляет роль и её permissions."""
    _require_admin(user)
    q = await session.execute(select(Role).where(Role.id == role_id))
    role = q.scalars().first()
    if not role:
        raise HTTPException(404, "Роль не найдена")

    role.name = payload.name.strip() or role.name
    role.description = payload.description

    codes = [c.strip() for c in payload.permissions if c.strip()]
    q2 = await session.execute(select(Permission).where(Permission.code.in_(codes)))
    exists = {p.code: p for p in q2.scalars().all()}
    new_perms = []
    for code in codes:
        perm = exists.get(code) or Permission(code=code)
        if not perm.id:
            session.add(perm)
            await session.flush()
        new_perms.append(perm)
    role.permissions = new_perms  # type: ignore[assignment]

    await session.commit()
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "permissions": [p.code for p in role.permissions],
    }


@router.delete("/adminpanel/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удаляет роль. Связи с пользователями также удаляются каскадом."""
    _require_admin(user)
    q = await session.execute(select(Role).where(Role.id == role_id))
    role = q.scalars().first()
    if not role:
        raise HTTPException(404, "Роль не найдена")
    await session.delete(role)
    await session.commit()
    return JSONResponse(status_code=204, content={})
