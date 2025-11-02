# -*- coding: utf-8 -*-
"""
Инициализация пакета моделей.
Агрегирует все ORM-модели, чтобы Alembic, FastAPI и админ-панель могли их импортировать из app.models.
"""

from app.db import Base

# ===== Пользователи / роли =====
from app.models.user import User  # если файл называется user.py
from app.models.role import Role  # если файл называется role.py
from app.models.user_role_link import UserRoleLink  # если отдельный файл, иначе адаптируй путь

# ===== Оборудование (новые модели) =====
from app.models.equipment import Line, Machine, Repair, RepairAttachment

__all__ = [
    "Base",
    "User",
    "Role",
    "UserRoleLink",
    "Line",
    "Machine",
    "Repair",
    "RepairAttachment",
]
