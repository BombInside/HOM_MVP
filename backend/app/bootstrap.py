from __future__ import annotations

from typing import Optional, Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import hash_password
from .models import Role, User


async def ensure_admin_user(session: AsyncSession) -> None:
    """Creates default roles and admin if missing"""
    # Получаем все роли
    result = await session.execute(cast(Any, select(Role)))
    existing_roles = {r.name for r in result.scalars().all()}

    # Создаём недостающие
    needed = {"Admin", "Technician"}
    for name in needed - existing_roles:
        session.add(Role(name=name))
    await session.commit()

    # Проверяем наличие пользователя admin
    stmt_admin = cast(Any, select(User).where(User.email == "admin@hom.local"))
    result = await session.execute(stmt_admin)
    admin: Optional[User] = result.scalars().first()

    if not admin:
        admin = User(
            email="admin@hom.local",
            password_hash=hash_password("admin"),
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

    # Привязываем роль Admin
    stmt_role = cast(Any, select(Role).where(Role.name == "Admin"))
    result = await session.execute(stmt_role)
    admin_role = result.scalars().first()
    if admin_role and admin_role not in (admin.roles or []):
        admin.roles = (admin.roles or []) + [admin_role]
        await session.commit()
