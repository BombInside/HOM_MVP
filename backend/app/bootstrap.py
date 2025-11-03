from __future__ import annotations

from typing import Any, Optional, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import hash_password
from .models import Role, User

from __future__ import annotations

# Пытаемся взять hash_password из app.auth, иначе — из app.security
try:
    from app.auth import hash_password  # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    try:
        from app.security import hash_password  # type: ignore
    except Exception:  # noqa: BLE001
        # Фоллбек: определите hash_password в одном из модулей, если этих нет
        def hash_password(raw: str) -> str:  # type: ignore[no-redef]
            import hashlib
            return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def ensure_admin_user(session: AsyncSession) -> None:
    """Создаёт базовые роли и пользователя admin при отсутствии."""
    # Роли
    result = await session.execute(cast(Any, select(Role)))
    existing_roles = {r.name for r in result.scalars().all()}

    needed = {"Admin", "Technician"}
    for name in needed - existing_roles:
        session.add(Role(name=name))
    await session.commit()

    # Пользователь admin
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

    # Привязка роли Admin
    stmt_role = cast(Any, select(Role).where(Role.name == "Admin"))
    result = await session.execute(stmt_role)
    admin_role = result.scalars().first()
    if admin_role and admin_role not in (admin.roles or []):
        admin.roles = (admin.roles or []) + [admin_role]
        await session.commit()
