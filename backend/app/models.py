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
    """
    Право доступа в системе (Permission).
    Используется для детализации возможностей ролей.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = Field(default=None)

    roles: List["Role"] = Relationship(back_populates="permissions", link_model=RolePermissionLink)


# ==========================
#  Модель Role (роль)
# ==========================

class Role(SQLModel, table=True):
    """
    Роль в системе (например: admin, operator, viewer, developer).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = Field(default=None)

    users: List["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)
    permissions: List[Permission] = Relationship(back_populates="roles", link_model=RolePermissionLink)


# ==========================
#  Модель User (пользователь)
# ==========================

class User(SQLModel, table=True):
    """
    Пользователь системы.
    Может иметь несколько ролей, которые определяют его права.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    roles: List[Role] = Relationship(back_populates="users", link_model=UserRoleLink)


# ==========================
#  Пример дополнительной модели (для контекста)
# ==========================

class Machine(SQLModel, table=True):
    """
    Пример вспомогательной модели (если есть в проекте).
    Используется, чтобы показать, как RBAC может управлять доступом к сущностям.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Line(SQLModel, table=True):
    """
    Модель производственной линии (Line).
    Используется в GraphQL и для управления оборудованием.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)
    description: Optional[str] = Field(default=None)


# ==========================
#  Системные служебные данные
# ==========================

class RBACSeed:
    """
    Служебный класс для начального заполнения ролей и разрешений.
    Используется при запуске приложения (startup event).
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
            "description": "Операционное управление, без доступа к настройкам и ролям",
            "permissions": [
                "view_dashboard",
                "manage_tasks",
                "view_logs",
            ],
        },
        "viewer": {
            "description": "Только чтение данных",
            "permissions": [
                "view_dashboard",
                "view_logs",
            ],
        },
        "developer": {
            "description": "Доступ к API, тестам и интеграциям",
            "permissions": [
                "view_dashboard",
                "use_api",
                "deploy_code",
            ],
        },
    }

    @classmethod
    async def seed(cls, session):
        """
        Автоматическое заполнение ролей и разрешений при первом запуске.
        """
        from sqlalchemy import select

        result = await session.execute(select(Role))
        existing_roles = result.scalars().all()

        # если таблица ролей пуста — создаём стандартные
        if not existing_roles:
            from app.models import Role, Permission, RolePermissionLink

            all_permissions: dict[str, Permission] = {}

            # создаём все permissions
            for role_name, role_data in cls.DEFAULT_ROLES.items():
                for perm_name in role_data["permissions"]:
                    if perm_name not in all_permissions:
                        perm = Permission(name=perm_name, description=f"Permission: {perm_name}")
                        session.add(perm)
                        all_permissions[perm_name] = perm

            await session.commit()

            # обновляем permissions из БД
            result = await session.execute(select(Permission))
            permissions = {p.name: p for p in result.scalars().all()}

            # создаём роли и назначаем им разрешения
            for role_name, role_data in cls.DEFAULT_ROLES.items():
                role = Role(name=role_name, description=role_data["description"])
                role.permissions = [permissions[p] for p in role_data["permissions"]]
                session.add(role)

            await session.commit()
            print("[RBAC] Default roles and permissions have been seeded.")


# ==========================
#  Подсказки для IDE и MyPy
# ==========================

__all__ = [
    "User",
    "Role",
    "Permission",
    "Machine",
    "UserRoleLink",
    "RolePermissionLink",
    "RBACSeed",
    "Line",
]

