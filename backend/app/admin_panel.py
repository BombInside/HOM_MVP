from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Sequence
import hashlib

from app.db import get_session
from app.models import User, Role

router = APIRouter(prefix="/adminpanel", tags=["Admin Panel"])
templates = Jinja2Templates(directory="app/templates")


# ==== Утилиты ====

def hash_password(password: str) -> str:
    """Хеширование пароля (демо)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


async def get_current_admin(request: Request, session: AsyncSession) -> Optional[User]:
    """Возвращает текущего пользователя из cookie-сессии, если он администратор."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    roles: Sequence[Role] = getattr(user, "roles", [])
    if any((getattr(r, "name", "") or "").lower() in ("admin", "administrator") for r in roles):
        return user
    return None


async def admin_exists(session: AsyncSession) -> bool:
    """Проверяет, существует ли хотя бы один администратор."""
    result_roles = await session.execute(select(Role))
    roles_all: Sequence[Role] = result_roles.scalars().all()
    admin_ids = [r.id for r in roles_all if (r.name or "").lower() in ("admin", "administrator")]
    if not admin_ids:
        return False

    result_users = await session.execute(select(User))
    users_all: Sequence[User] = result_users.scalars().all()
    for user in users_all:
        roles: Sequence[Role] = getattr(user, "roles", [])
        for role in roles:
            if role.id in admin_ids:
                return True
    return False


# ==== Роуты ====

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница логина."""
    error = request.query_params.get("err")
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": error})


@router.post("/login", response_class=HTMLResponse)
async def login_action(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """Авторизация администратора."""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or user.hashed_password != hash_password(password):
        return RedirectResponse("/adminpanel/login?err=Неверный+логин+или+пароль", status_code=status.HTTP_303_SEE_OTHER)

    roles: Sequence[Role] = getattr(user, "roles", [])
    if not any((getattr(r, "name", "") or "").lower() in ("admin", "administrator") for r in roles):
        return RedirectResponse("/adminpanel/login?err=Недостаточно+прав", status_code=status.HTTP_303_SEE_OTHER)

    request.session["user_id"] = user.id
    return RedirectResponse("/adminpanel", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
async def logout(request: Request):
    """Выход из панели."""
    request.session.clear()
    return RedirectResponse("/adminpanel/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/", response_class=HTMLResponse)
async def admin_home(request: Request, session: AsyncSession = Depends(get_session)):
    """Главная страница панели."""
    user = await get_current_admin(request, session)
    if not user:
        return RedirectResponse("/adminpanel/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("admin_home.html", {"request": request, "user": user})


@router.get("/bootstrap", response_class=HTMLResponse)
async def bootstrap_page(request: Request, session: AsyncSession = Depends(get_session)):
    """Мастер создания администратора."""
    if await admin_exists(session):
        return RedirectResponse("/adminpanel/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("admin_bootstrap.html", {"request": request})


@router.post("/bootstrap", response_class=HTMLResponse)
async def bootstrap_action(
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """Создание администратора (если его нет)."""
    if await admin_exists(session):
        return RedirectResponse("/adminpanel/login", status_code=status.HTTP_303_SEE_OTHER)

    # Проверяем наличие роли admin
    result_role = await session.execute(select(Role).where(Role.name == "admin"))
    role = result_role.scalar_one_or_none()
    if not role:
        role = Role(name="admin", description="Administrator with full access")
        session.add(role)
        await session.commit()
        await session.refresh(role)

    # Создаём пользователя и добавляем роль
    user = User(email=email, hashed_password=hash_password(password))
    if hasattr(user, "roles"):
        user.roles.append(role)
    session.add(user)
    await session.commit()
    return RedirectResponse("/adminpanel/login?created=1", status_code=status.HTTP_303_SEE_OTHER)
