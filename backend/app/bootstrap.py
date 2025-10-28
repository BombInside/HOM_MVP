# Bootstrap utility to ensure database exists and seed admin user and roles.
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from sqlmodel import select
import asyncio
from .config import settings
from .db import async_session
from .models import User, Role
from .auth import hash_password

async def ensure_db_exists():
    engine_sys = create_async_engine(settings.db_url, echo=False)
    async with engine_sys.begin() as conn:
        await conn.execute(text("CREATE DATABASE IF NOT EXISTS hom"))
    await engine_sys.dispose()

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
    await ensure_db_exists()
    await seed_admin()

if __name__ == "__main__":
    asyncio.run(main())