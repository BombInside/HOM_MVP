# -*- coding: utf-8 -*-
"""
Единая точка импорта для всех моделей проекта.
"""
from app.models.base import Base
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.links import UserRoleLink, RolePermissionLink
from app.models.admin_menu_link import AdminMenuLink
from app.models.equipment import Line, Machine, Repair, RepairAttachment

__all__ = [
    "Base",
    "User",
    "Role",
    "Permission",
    "UserRoleLink",
    "RolePermissionLink",
    "AdminMenuLink",
    "Line",
    "Machine",
    "Repair",
    "RepairAttachment",
]
