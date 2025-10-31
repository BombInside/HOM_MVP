from fastapi import (
    APIRouter,
    Request,
    Depends,
    Form,
    status,
    HTTPException,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, cast, String
from typing import Optional, Sequence, List, Callable, Awaitable, Any
import hashlib

from app.db import get_session
from app.models import User, Role, Permission, RBACSeed
from sqlalchemy import literal

router = APIRouter(prefix="/adminpanel", tags=["Admin Panel"])
templates = Jinja2Templates(directory="app/templates")


# ======================================================
# Утилиты
# ======================================================

def hash_password(password: str) -> str:
    """Хеширование пароля (демо)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


async def admin_exists(session: AsyncSession) -> bool:
    """Проверяет, есть ли хотя бы один пользователь с ролью admin."""
    result_roles = await session.execute(select(Role))
    all_roles: Sequence[Role] = result_roles.scalars().all()
    admin_role_ids = [r.id for r in all_roles if r.name and r.name.lower() in ("admin", "administrator")]

    if not admin_role_ids:
        return False

    result_users = await session.execute(select(User))
    all_users: Sequence[User] = result_users.scalars().all()
    for user in all_users:
        user_roles = getattr(user, "roles", [])
        if any(r.id and r.id in admin_role_ids for r in user_roles):
            return True
    return False


async def get_current_user(request: Request, session: AsyncSession) -> Optional[User]:
    """Возвращает текущего пользователя из сессии."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    res = await session.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


async def get_current_admin(request: Request, session: AsyncSession) -> Optional[User]:
    """Проверяет, является ли текущий пользователь администратором."""
    user = await get_current_user(request, session)
    if not user:
        return None
    for role in getattr(user, "roles", []):
        if role.name and role.name.lower() in ("admin", "administrator"):
            return user
    return None


# ======================================================
# RBAC-декоратор
# ======================================================

def require_permission(permission_name: str) -> Callable[..., Awaitable[User]]:
    """
    Зависимость для проверки наличия разрешения у пользователя.
    Возвращает текущего пользователя, если у него есть нужное разрешение.
    """

    async def dependency(
        request: Request,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        user = await get_current_user(request, session)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не авторизован")

        for role in getattr(user, "roles", []):
            for perm in getattr(role, "permissions", []):
                if perm.name == permission_name:
                    return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Недостаточно прав: {permission_name}",
        )

    return dependency


# ======================================================
# Bootstrap-страницы
# ======================================================

@router.get("/bootstrap", response_class=HTMLResponse)
async def bootstrap_page(request: Request, session: AsyncSession = Depends(get_session)):
    """Страница для создания администратора, если его нет."""
    exists = await admin_exists(session)
    return templates.TemplateResponse(
        "admin_bootstrap.html",
        {"request": request, "admin_exists": exists, "admin_created": False},
    )


@router.post("/bootstrap", response_class=HTMLResponse)
async def bootstrap_action(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """Создание первого администратора."""
    if await admin_exists(session):
        return templates.TemplateResponse(
            "admin_bootstrap.html",
            {"request": request, "admin_exists": True, "admin_created": False},
        )

    # ищем или создаём роль администратора
    res = await session.execute(
        select(Role).where(literal(True).op("AND")(Role.name.in_(["admin", "administrator"])))  # type: ignore[arg-type]
    )
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name="admin", description="Administrator with full access")
        session.add(role)
        await session.commit()
        await session.refresh(role)

    # создаём пользователя
    user = User(email=email, hashed_password=hash_password(password))
    user.roles.append(role)
    session.add(user)
    await session.commit()

    return templates.TemplateResponse(
        "admin_bootstrap.html",
        {"request": request, "admin_exists": True, "admin_created": True},
    )



# ======================================================
# Авторизация и выход
# ======================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа администратора."""
    error = request.query_params.get("err")
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": error})


@router.post("/login")
async def login_action(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """Авторизация пользователя с проверкой ролей."""
    res = await session.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user or user.hashed_password != hash_password(password):
        return RedirectResponse("/adminpanel/login?err=Неверный+логин+или+пароль", status_code=status.HTTP_303_SEE_OTHER)

    roles = getattr(user, "roles", [])
    if not any(r.name and r.name.lower() in ("admin", "administrator") for r in roles):
        return RedirectResponse("/adminpanel/login?err=Недостаточно+прав", status_code=status.HTTP_303_SEE_OTHER)

    request.session["user_id"] = user.id
    return RedirectResponse("/adminpanel", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
async def logout(request: Request):
    """Выход из панели администратора."""
    request.session.clear()
    return RedirectResponse("/adminpanel/login", status_code=status.HTTP_303_SEE_OTHER)


# ======================================================
# Главная страница панели
# ======================================================

@router.get("/", response_class=HTMLResponse)
async def admin_home(request: Request, session: AsyncSession = Depends(get_session)):
    """Главная страница панели администратора."""
    user = await get_current_admin(request, session)
    if not user:
        return RedirectResponse("/adminpanel/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("admin_home.html", {"request": request, "user": user})


# ======================================================
# Управление ролями и разрешениями
# ======================================================

@router.get("/roles", response_class=HTMLResponse)
async def list_roles(
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("manage_roles")),
):
    """Отображает список ролей и разрешений."""
    res = await session.execute(select(Role))
    roles: List[Role] = list(res.scalars().all())
    return templates.TemplateResponse(
        "admin_roles.html",
        {"request": request, "roles": roles, "user": user},
    )


@router.get("/roles/new", response_class=HTMLResponse)
async def new_role_page(
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("manage_roles")),
):
    """Страница создания новой роли."""
    res = await session.execute(select(Permission))
    perms: List[Permission] = list(res.scalars().all())
    return templates.TemplateResponse(
        "admin_role_form.html",
        {"request": request, "permissions": perms, "user": user},
    )


@router.post("/roles/new")
async def create_role(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    permissions: Optional[List[int]] = Form(default=None),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("manage_roles")),
):
    """Создание новой роли и назначение прав."""
    new_role = Role(name=name, description=description)
    if permissions:
        valid_ids = [int(pid) for pid in permissions if pid]
        if valid_ids:
            res = await session.execute(select(Permission).where(Permission.id.in_(valid_ids)))  # type: ignore[arg-type, union-attr]
            perms: List[Permission] = list(res.scalars().all())
            new_role.permissions = perms
    session.add(new_role)
    await session.commit()
    return RedirectResponse("/adminpanel/roles", status_code=status.HTTP_303_SEE_OTHER)


# ======================================================
# Автосоздание ролей и прав при запуске
# ======================================================

@router.on_event("startup")
async def seed_default_roles() -> None:
    """Создание стандартных ролей и разрешений при первом запуске."""
    from app.db import async_session
    async with async_session() as session:
        await RBACSeed.seed(session)
