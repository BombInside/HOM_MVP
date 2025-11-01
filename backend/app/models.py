# -*- coding: utf-8 -*-
"""
Базовые модели пользователей/ролей/прав для RBAC.
"""
from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint


class UserRoleLink(SQLModel, table=True):
    """Промежуточная таблица many-to-many между пользователем и ролью."""
    __tablename__ = "user_role_link"
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    role_id: int = Field(foreign_key="role.id", primary_key=True)


class RolePermissionLink(SQLModel, table=True):
    """Промежуточная таблица many-to-many между ролью и правом."""
    __tablename__ = "role_permission_link"
    role_id: int = Field(foreign_key="role.id", primary_key=True)
    permission_id: int = Field(foreign_key="permission.id", primary_key=True)


class User(SQLModel, table=True):
    """Пользователь системы."""
    __tablename__ = "user"
    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # связи
    roles: list["Role"] = Relationship(
        back_populates="users",
        link_model=UserRoleLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Role(SQLModel, table=True):
    """Роль пользователя (набор прав)."""
    __tablename__ = "role"
    __table_args__ = (UniqueConstraint("name", name="uq_role_name"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    description: Optional[str] = Field(default=None)

    # связи
    users: list[User] = Relationship(
        back_populates="roles",
        link_model=UserRoleLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    permissions: list["Permission"] = Relationship(
        back_populates="roles",
        link_model=RolePermissionLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Permission(SQLModel, table=True):
    """Единичное право (действие на сущности)."""
    __tablename__ = "permission"
    __table_args__ = (UniqueConstraint("code", name="uq_permission_code"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, nullable=False)  # например: machines.read, machines.write
    description: Optional[str] = Field(default=None)

    # связи
    roles: list[Role] = Relationship(
        back_populates="permissions",
        link_model=RolePermissionLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
