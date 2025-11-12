# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ==========================
# Permissions DTOs
# ==========================
class PermissionOut(BaseModel):
    """Схема для отображения права (только чтение)."""
    id: int
    code: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================
# Role DTOs
# ==========================
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Для создания: принимает список кодов прав."""
    permission_codes: List[str] = []


class RoleUpdate(BaseModel):
    """Для обновления: все поля опциональны, включая список кодов прав."""
    name: Optional[str] = None
    description: Optional[str] = None
    permission_codes: Optional[List[str]] = None


class RoleOut(RoleBase):
    """Для чтения: возвращает объекты Permission."""
    id: int
    permissions: List[PermissionOut]
    
    model_config = ConfigDict(from_attributes=True)