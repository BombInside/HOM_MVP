# -*- coding: utf-8 -*-
"""
Инициализация пакета моделей.
Агрегирует все ORM-модели, чтобы Alembic, FastAPI и админ-панель могли их импортировать из app.models.
ВНИМАНИЕ: здесь мы импортируем Base из app.db — единая точка истины для декларативной базы.
"""

from __future__ import annotations

from app.db import Base

# ===== Пользователи / роли (пути подгони под фактические файлы) =====
# Если у тебя файлы называются иначе, просто поправь пути ниже.
from app.models.user import User  # например, app/models/user.py
from app.models.role import Role  # например, app/models/role.py
from app.models.user_role_link import UserRoleLink  # например, app/models/user_role_link.py

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
