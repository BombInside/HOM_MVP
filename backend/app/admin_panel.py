from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
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
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        return None

    # Проверка роли
    role_name = None
    try:
        if getattr(user, "role", None) and getattr(user.role, "name", None):
            role_name = user.role.name
    except Exception:
        pass

    if not role_name and getattr(user, "role_id", None):
        r = await session.execute(select(Role).where(Role.id == user.role_id))
        role = r.scalar_one_or_none()
        role_name = role.name if role else None

    if role_name and role_name.lower() in ("admin", "administrator"):
        return user
    return None

async def admin_exists(session: AsyncSession) -> bool:
    """Проверяет, существует ли хотя бы один администратор."""
    roles = await session.execute(select(Role).where(Role.name.in_(["admin", "administrator"])))
    role_ids = [r.id for r in roles.scalars().all()]
    if not role_ids:
        return False
    users = await session.execute(select(User).where(User.role_id.in_(role_ids)))
    return users.scalars().first() is not None

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
    user_res = await session.execute(select(User).where(User.email == email))
    user = user_res.scalar_one_or_none()
    if not user or user.hashed_password != hash_password(password):
        return RedirectResponse("/adminpanel/login?err=Неверный+логин+или+пароль", status_code=status.HTTP_303_SEE_OTHER)

    # Проверка роли
    role_ok = False
    if getattr(user, "role", None) and getattr(user.role, "name", None):
        role_ok = user.role.name.lower() in ("admin", "administrator")
    elif getattr(user, "role_id", None):
        role_res = await session.execute(select(Role).where(Role.id == user.role_id))
        role = role_res.scalar_one_or_none()
        role_ok = bool(role and role.name and role.name.lower() in ("admin", "administrator"))

    if not role_ok:
        return RedirectResponse("/adminpanel/login?err=Недостаточно+прав", status_code=status.HTTP_303_SEE_OTHER)

    # Сохраняем user_id в сессии
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

    # Проверяем роль admin
    role_res = await session.execute(select(Role).where(Role.name == "admin"))
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(name="admin", description="Administrator with full access")
        session.add(role)
        await session.commit()
        await session.refresh(role)

    # Создаём пользователя
    user = User(email=email, hashed_password=hash_password(password), role_id=role.id)
    session.add(user)
    await session.commit()
    return RedirectResponse("/adminpanel/login?created=1", status_code=status.HTTP_303_SEE_OTHER)
