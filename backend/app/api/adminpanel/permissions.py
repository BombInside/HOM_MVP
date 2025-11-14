# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_session
from app.auth import admin_required
from app.models import Permission
from app.schemas.role import PermissionOut


router = APIRouter(
    prefix="/permissions",
    tags=["Admin Permissions"],
)


@router.get(
    "/",
    response_model=List[PermissionOut],
    dependencies=[Depends(admin_required)],
)
async def list_permissions(db: AsyncSession = Depends(get_session)) -> List[PermissionOut]:
    """
    Получить полный список прав (permissions) для админ-панели.

    Доступ только для администратора (admin_required).
    """
    result = await db.scalars(select(Permission).order_by(Permission.code))
    permissions = result.all()
    # Pydantic v2: используем model_validate для from_attributes
    return [PermissionOut.model_validate(p) for p in permissions]
