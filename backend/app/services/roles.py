# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Optional, Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.services.base import CRUDServiceBase
from app.models import Role, Permission, RolePermissionLink
from app.schemas.role import RoleCreate, RoleUpdate, RoleOut

class RoleService(CRUDServiceBase[Role, RoleCreate, RoleUpdate]):
    """
    Сервис для управления ролями с поддержкой связей many-to-many (Permissions).
    """

    async def _get_permissions_by_codes(self, db: AsyncSession, codes: List[str]) -> List[Permission]:
        """Получает объекты Permission по списку кодов."""
        if not codes:
            return []
            
        stmt = select(Permission).where(Permission.code.in_(codes))
        result = await db.execute(stmt)
        permissions = list(result.scalars().all())

        if len(permissions) != len(codes):
            # Проверяем, не были ли переданы несуществующие коды
            found_codes = {p.code for p in permissions}
            missing_codes = list(set(codes) - found_codes)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Несуществующие права: {', '.join(missing_codes)}",
            )
        return permissions


    async def create(self, db: AsyncSession, obj_in: RoleCreate) -> Role:
        """Создает роль и привязывает права."""
        # Извлекаем коды прав перед созданием объекта ORM
        permission_codes = obj_in.permission_codes
        
        # Создаем данные для Role без списка permission_codes
        role_data = obj_in.model_dump(exclude={"permission_codes"})

        # Создаем объект Role
        new_role = Role(**role_data)
        db.add(new_role)
        
        # Загружаем объекты Permission и привязываем их к новой роли
        permissions = await self._get_permissions_by_codes(db, permission_codes)
        new_role.permissions = permissions
        
        await db.commit()
        await db.refresh(new_role)
        return new_role


    async def update(self, db: AsyncSession, obj_id: int, obj_in: RoleUpdate) -> Role:
        """Обновляет роль и привязки прав."""
        db_obj = await self.get_or_404(db, obj_id)

        data = obj_in.model_dump(exclude_unset=True)
        permission_codes: Optional[List[str]] = data.pop("permission_codes", None)
        
        # 1. Обновляем базовые поля
        for field, value in data.items():
            setattr(db_obj, field, value)

        # 2. Обновляем связи с правами
        if permission_codes is not None:
            permissions = await self._get_permissions_by_codes(db, permission_codes)
            db_obj.permissions = permissions # SQLAlchemy автоматически управляет связующей таблицей
            
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def list_permissions(self, db: AsyncSession) -> List[Permission]:
        """Получает список всех доступных прав (для UI)."""
        result = await db.execute(select(Permission).order_by(Permission.code))
        return list(result.scalars().all())

role_service = RoleService(Role)