from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


# ==========================
#  Базовые связи Many-to-Many
# ==========================

class UserRoleLink(SQLModel, table=True):
    """Связь многие-ко-многим между пользователями и ролями."""
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)


class RolePermissionLink(SQLModel, table=True):
    """Связь многие-ко-многим между ролями и разрешениями."""
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)
    permission_id: Optional[int] = Field(default=None, foreign_key="permission.id", primary_key=True)


# ==========================
#  Модель Permission (права)
# ==========================

class Permission(SQLModel, table=True):
    """Право доступа (Permission)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None

    roles: List["Role"] = Relationship(back_populates="permissions", link_model=RolePermissionLink)


# ==========================
#  Модель Role (роль)
# ==========================

class Role(SQLModel, table=True):
    """Роль в системе (admin, operator, viewer, developer)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None

    users: List["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)
    permissions: List[Permission] = Relationship(back_populates="roles", link_model=RolePermissionLink)


# ==========================
#  Модель User (пользователь)
# ==========================

class User(SQLModel, table=True):
    """Пользователь системы."""
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    roles: List[Role] = Relationship(back_populates="users", link_model=UserRoleLink)


# ==========================
#  Пример модели
# ==========================

class Machine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==========================
#  Служебный класс RBACSeed
# ==========================

class RBACSeed:
    """
    Служебный класс для начального заполнения ролей и разрешений.
    Безопасен к повторным вызовам (не создаёт дубликаты).
    """

    DEFAULT_ROLES = {
        "admin": {
            "description": "Полный доступ ко всем функциям системы",
            "permissions": [
                "manage_users",
                "manage_roles",
                "view_dashboard",
                "edit_settings",
                "view_logs",
            ],
        },
        "operator": {
            "description": "Управление задачами без доступа к настройкам",
            "permissions": ["view_dashboard", "manage_tasks", "view_logs"],
        },
        "viewer": {
            "description": "Только чтение данных",
            "permissions": ["view_dashboard", "view_logs"],
        },
        "developer": {
            "description": "Доступ к API и DevOps-инструментам",
            "permissions": ["view_dashboard", "use_api", "deploy_code"],
        },
    }

    @classmethod
    async def seed(cls, session) -> None:
        """Создаёт роли и разрешения, если они ещё не существуют."""
        from sqlalchemy import select

        # Проверяем, есть ли хоть одна роль
        result = await session.execute(select(Role))
        existing_roles = result.scalars().all()

        if existing_roles:
            print("🔁 RBAC роли уже существуют, пропускаем инициализацию.")
            return

        print("🚀 Создание стандартных ролей и разрешений...")

        # Создаём все уникальные разрешения
        permissions_map: dict[str, Permission] = {}
        for role_data in cls.DEFAULT_ROLES.values():
            for perm_name in role_data["permissions"]:
                if perm_name not in permissions_map:
                    perm = Permission(name=perm_name, description=f"Permission: {perm_name}")
                    session.add(perm)
                    permissions_map[perm_name] = perm

        await session.commit()

        # Обновляем список разрешений
        result = await session.execute(select(Permission))
        permissions_by_name = {p.name: p for p in result.scalars().all()}

        # Создаём роли
        for role_name, role_data in cls.DEFAULT_ROLES.items():
            role = Role(name=role_name, description=role_data["description"])
            role.permissions = [permissions_by_name[p] for p in role_data["permissions"]]
            session.add(role)

        await session.commit()
        print("✅ RBAC роли и разрешения успешно созданы.")


__all__ = [
    "User",
    "Role",
    "Permission",
    "Machine",
    "UserRoleLink",
    "RolePermissionLink",
    "RBACSeed",
]
