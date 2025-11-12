# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db import get_session
from app.auth import admin_required
from app.services.roles import role_service
from app.schemas.role import RoleOut, RoleCreate, RoleUpdate, PermissionOut
from app.models import Role


router = APIRouter(prefix="/roles", tags=["Admin Roles"])


@router.get("/permissions", response_model=List[PermissionOut], dependencies=[Depends(admin_required)])
async def list_permissions(db: AsyncSession = Depends(get_session)) -> List[PermissionOut]:
    """
    Получить список всех доступных прав (permissions) в системе.
    Требует прав администратора.
    """
    permissions = await role_service.list_permissions(db)
    return [PermissionOut.model_validate(p) for p in permissions]


@router.get("/", response_model=List[RoleOut], dependencies=[Depends(admin_required)])
async def list_roles(db: AsyncSession = Depends(get_session)) -> List[RoleOut]:
    """
    Получить список всех ролей.
    Требует прав администратора.
    """
    roles = await role_service.list(db)
    return [RoleOut.model_validate(r) for r in roles]


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(admin_required)])
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_session)) -> RoleOut:
    """
    Создать новую роль с указанными правами.
    Требует прав администратора.
    """
    try:
        new_role = await role_service.create(db, data)
        return RoleOut.model_validate(new_role)
    except IntegrityError as e:
        # Обработка ошибки уникальности имени роли
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Роль с таким именем уже существует.")
    except HTTPException:
        # Прокидываем ошибки из сервиса (например, несуществующие права)
        raise


@router.get("/{role_id}", response_model=RoleOut, dependencies=[Depends(admin_required)])
async def get_role(role_id: int, db: AsyncSession = Depends(get_session)) -> RoleOut:
    """
    Получить роль по ID.
    Требует прав администратора.
    """
    role = await role_service.get_or_404(db, role_id)
    return RoleOut.model_validate(role)


@router.put("/{role_id}", response_model=RoleOut, dependencies=[Depends(admin_required)])
async def update_role(role_id: int, data: RoleUpdate, db: AsyncSession = Depends(get_session)) -> RoleOut:
    """
    Обновить существующую роль и ее права.
    Требует прав администратора.
    """
    try:
        updated_role = await role_service.update(db, role_id, data)
        return RoleOut.model_validate(updated_role)
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Роль с таким именем уже существует.")
    except HTTPException:
        raise


@router.delete("/{role_id}", dependencies=[Depends(admin_required)])
async def delete_role(role_id: int, db: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """
    Удалить роль по ID.
    Требует прав администратора.
    """
    await role_service.delete(db, role_id) # Используем жесткое удаление, так как у Role нет soft_delete
    return {"message": "Role deleted"}