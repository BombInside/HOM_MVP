# Bootstrap utility to ensure database exists and seed admin user and roles.
# EN: Removed create_async_engine and text imports (no need to manually create DB)
# RU: Удалены импорты create_async_engine и text (нет необходимости вручную создавать БД)
from sqlmodel import select
import asyncio
from .config import settings
from .db import async_session
from .models import User, Role
from .auth import hash_password

# 💡 EN: Removed 'async def ensure_db_exists()' as Postgres container creates the DB automatically.
# 💡 RU: Удалена 'async def ensure_db_exists()', так как контейнер Postgres создает БД автоматически.

async def seed_admin():
    # EN: Only seed admin user and roles in development environment (SECURITY FIX)
    # RU: Создаем администратора и роли только в среде разработки (ИСПРАВЛЕНИЕ БЕЗОПАСНОСТИ)
    if settings.app_env != "dev":
        # EN: Log that seeding is skipped
        # RU: Логируем, что seeding пропущен
        print("Skipping admin seed and role creation outside of development environment.")
        return

    async with async_session() as session:
        # EN: Role creation logic
        # RU: Логика создания ролей
        for rn in ["Operator", "Technician", "Supervisor", "Manager", "Admin", "SystemAdmin"]:
            res = await session.execute(select(Role).where(Role.name == rn))
            if not res.scalar_one_or_none():
                session.add(Role(name=rn, description=f"Role {rn}"))
                
        # EN: Admin user creation logic
        # RU: Логика создания Admin пользователя
        res = await session.execute(select(User).where(User.email=="admin@hom.local"))
        if not res.scalar_one_or_none():
            session.add(User(email="admin@hom.local", hashed_password=hash_password("admin123")))
        await session.commit()

async def main():
    # EN: Removed call to ensure_db_exists
    # RU: Удален вызов ensure_db_exists
    await seed_admin()

if __name__ == "__main__":
    asyncio.run(main())