# -*- coding: utf-8 -*-
"""
Маршруты админ-панели:
- Одноразовый bootstrap для создания первого администратора
- Редактор ролей и прав
Примечание: для простоты используем JSON формы (application/json) и минимальный HTML вывод.
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_session
from .models import User, Role, Permission, RolePermissionLink, UserRoleLink
from .security import hash_password
from .auth import get_current_user

router = APIRouter(tags=["admin-panel"])
settings = get_settings()


async def _admin_exists(session: AsyncSession) -> bool:
    """
    Проверяет, существует ли в системе хотя бы один пользователь с ролью 'admin'.
    """
    q = await session.execute(select(Role).where(Role.name == "admin"))
    admin_role = q.scalars().first()
    if not admin_role:
        return False
    # Проверяем связку
    q2 = await session.execute(select(UserRoleLink).where(UserRoleLink.role_id == admin_role.id))
    link = q2.first()
    return link is not None


@router.get("/health", include_in_schema=False)
async def health() -> dict:
    """Проверка живости сервиса для healthcheck контейнера/nginx."""
    return {"status": "ok"}


@router.get(settings.ADMIN_BOOTSTRAP_PATH, response_class=HTMLResponse, include_in_schema=False)
async def admin_bootstrap_form(request: Request, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    """
    HTML форма для создания первого администратора.
    Доступна ТОЛЬКО пока администратора нет.
    После создания — редирект на '/' и всплывающее сообщение.
    """
    if await _admin_exists(session):
        # Форма закрыта
        return HTMLResponse(
            "<html><body><script>window.location='/'</script>"
            "<p>Пользователь с правами администратора уже существует. "
            "Форма бустрапа выключена.</p></body></html>",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    html = """
    <html>
      <body>
        <h1>Bootstrap администратора</h1>
        <form method="post" action="{path}">
          <label>Email: <input type="email" name="email" required/></label><br/>
          <label>Пароль: <input type="password" name="password" required/></label><br/>
          <button type="submit">Создать</button>
        </form>
      </body>
    </html>
    """.format(path=settings.ADMIN_BOOTSTRAP_PATH)
    return HTMLResponse(html)


@router.post(settings.ADMIN_BOOTSTRAP_PATH, include_in_schema=False)
async def admin_bootstrap_post(request: Request, session: AsyncSession = Depends(get_session)) -> RedirectResponse:
    """
    Обработчик создания первого администратора.
    После успешного создания — редирект на '/'.
    Если админ уже есть — форма закрыта, редирект на '/'.
    """
    if await _admin_exists(session):
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie("toast", "Администратор уже существует", httponly=False)
        return response

    form = await request.form()
    email = str(form.get("email", "")).strip().lower()
    password = str(form.get("password", "")).strip()
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email и пароль обязательны")

    # создаём роль admin если нет
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

    # редирект на главную и set-cookie для всплывашки
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("toast", "Администратор создан", httponly=False)
    return response


# -------------------- Редактор ролей и прав --------------------

def _require_admin(user: User) -> None:
    """Проверяем, что у пользователя есть роль admin."""
    if not any(r.name == "admin" for r in user.roles):
        raise HTTPException(status_code=403, detail="Admin role required")


@router.get("/adminpanel/roles", response_class=JSONResponse)
async def list_roles(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Возвращает список ролей и их прав (для интерфейса редактора)."""
    _require_admin(user)
    q = await session.execute(select(Role))
    roles = q.scalars().all()
    result = []
    for role in roles:
        # грузим права
        permissions = [p.code for p in role.permissions]
        result.append({"id": role.id, "name": role.name, "description": role.description, "permissions": permissions})
    return result


class RoleUpsertPayload(dict):
    """Простая полезная нагрузка для create/update роли (через JSON)."""
    name: str
    description: Optional[str]
    permissions: List[str]


@router.post("/adminpanel/roles", response_class=JSONResponse)
async def create_role(
    payload: RoleUpsertPayload,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Создаёт новую роль и назначает список permissions (по code)."""
    _require_admin(user)
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(400, "Поле name обязательно")

    role = Role(name=name, description=payload.get("description"))
    session.add(role)
    await session.flush()

    # Подтягиваем/создаём permissions по code
    codes = [c.strip() for c in payload.get("permissions", []) if c.strip()]
    if codes:
        # существующие
        from sqlmodel import or_
        q = await session.execute(select(Permission).where(Permission.code.in_(codes)))
        exists = {p.code: p for p in q.scalars().all()}
        # создаём недостающие
        to_add = []
        for code in codes:
            perm = exists.get(code) or Permission(code=code)
            if not perm.id:
                session.add(perm)
                await session.flush()
            to_add.append(perm)
        role.permissions = to_add  # type: ignore[assignment]

    await session.commit()
    return {"id": role.id, "name": role.name, "description": role.description, "permissions": [p.code for p in role.permissions]}


@router.put("/adminpanel/roles/{role_id}", response_class=JSONResponse)
async def update_role(
    role_id: int,
    payload: RoleUpsertPayload,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Обновляет роль и её permissions (список code)."""
    _require_admin(user)

    q = await session.execute(select(Role).where(Role.id == role_id))
    role = q.scalars().first()
    if not role:
        raise HTTPException(404, "Роль не найдена")

    role.name = str(payload.get("name", role.name)).strip() or role.name
    role.description = payload.get("description")

    codes = [c.strip() for c in payload.get("permissions", []) if c.strip()]
    # Грузим существующие и создаём новые
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
    return {"id": role.id, "name": role.name, "description": role.description, "permissions": [p.code for p in role.permissions]}


@router.delete("/adminpanel/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Удаляет роль. Связи с пользователями также удаляются (через каскад внешних ключей на уровне БД)."""
    _require_admin(user)

    q = await session.execute(select(Role).where(Role.id == role_id))
    role = q.scalars().first()
    if not role:
        raise HTTPException(404, "Роль не найдена")

    await session.delete(role)
    await session.commit()
    return JSONResponse(status_code=204, content={})
