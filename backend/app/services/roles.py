# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.services.base import CRUDServiceBase
from app.models import Role, Permission
from app.schemas.role import RoleCreate, RoleUpdate


class RoleService(CRUDServiceBase[Role, RoleCreate, RoleUpdate]):
    """
    Сервис для управления ролями с поддержкой связей many-to-many (Permissions).
    """

    # ============================================================
    # FIX: ПОЛНОСТЬЮ ПЕРЕОПРЕДЕЛЯЕМ list(), ЧТОБЫ ОН ВСЕГДА
    #      ВОЗВРАЩАЛ ИМЕННО СПИСОК [Role, Role, ...]
    # ============================================================
    async def list(self, db: AsyncSession) -> List[Role]:
        """
        Возвращает СТРОГО список ролей (List[Role])
        чтобы фронтенд мог безопасно вызывать .filter()
        """
        result = await db.scalars(select(Role).order_by(Role.name))
        return list(result.all())

    # ============================================================
    async def _get_permissions_by_codes(self, db: AsyncSession, codes: List[str]) -> List[Permission]:
        """Получает объекты Permission по списку кодов."""
        if not codes:
            return []

        stmt = select(Permission).where(Permission.code.in_(codes))
        result = await db.execute(stmt)
        permissions = list(result.scalars().all())

        if len(permissions) != len(codes):
            found_codes = {p.code for p in permissions}
            missing_codes = list(set(codes) - found_codes)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Несуществующие права: {', '.join(missing_codes)}",
            )
        return permissions

    async def create(self, db: AsyncSession, obj_in: RoleCreate) -> Role:
        """Создаёт роль и привязывает права."""
        permission_codes = obj_in.permission_codes
        role_data = obj_in.model_dump(exclude={"permission_codes"})

        new_role = Role(**role_data)
        db.add(new_role)

        permissions = await self._get_permissions_by_codes(db, permission_codes)
        new_role.permissions = permissions

        await db.commit()
        await db.refresh(new_role)
        return new_role

    async def update(self, db: AsyncSession, obj_id: int, obj_in: RoleUpdate) -> Role:
        """Обновляет роль и её permissions."""
        db_obj = await self.get_or_404(db, obj_id)
        data = obj_in.model_dump(exclude_unset=True)
        permission_codes: Optional[List[str]] = data.pop("permission_codes", None)

        # Обновляем простые поля
        for field, value in data.items():
            setattr(db_obj, field, value)

        # Обновляем permissions
        if permission_codes is not None:
            permissions = await self._get_permissions_by_codes(db, permission_codes)
            db_obj.permissions = permissions

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def list_permissions(self, db: AsyncSession) -> List[Permission]:
        """Возвращает список всех permissions."""
        result = await db.scalars(select(Permission).order_by(Permission.code))
        return list(result.all())


role_service = RoleService(Role)
