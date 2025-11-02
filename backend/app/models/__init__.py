# -*- coding: utf-8 -*-
"""
Агрегатор всех ORM-моделей проекта.
Импортирует Base и все модели, чтобы Alembic и FastAPI могли видеть их.
"""

from __future__ import annotations

# Базовый класс и модели пользователей, ролей и прав — из models.py
from app.models.models import (
    Base,
    User,
    Role,
    UserRoleLink,
    RolePermissionLink,
    Permission,
    AdminMenuLink,
)

# Модели производственного оборудования — из equipment.py
from app.models.equipment import (
    Line,
    Machine,
    Repair,
    RepairAttachment,
)

__all__ = [
    # база
    "Base",
    # пользователи / роли / права
    "User",
    "Role",
    "UserRoleLink",
    "RolePermissionLink",
    "Permission",
    "AdminMenuLink",
    # оборудование
    "Line",
    "Machine",
    "Repair",
    "RepairAttachment",
]
