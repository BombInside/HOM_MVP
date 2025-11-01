# app/models.py
# -*- coding: utf-8 -*-
"""
Модели данных для RBAC: пользователи, роли и права.
Совместимо с SQLAlchemy 2.x и SQLModel 0.0.16+.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


# ---------- БАЗОВЫЙ КЛАСС ----------
class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


# ---------- ЛИНК-ТАБЛИЦЫ ----------
class UserRoleLink(Base):
    """Связь many-to-many между пользователями и ролями."""
    __tablename__ = "user_role_link"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), primary_key=True)


class RolePermissionLink(Base):
    """Связь many-to-many между ролями и правами."""
    __tablename__ = "role_permission_link"

    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permission.id"), primary_key=True)


# ---------- ОСНОВНЫЕ МОДЕЛИ ----------
class User(Base):
    """Пользователь системы."""
    __tablename__ = "user"
    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    roles: Mapped[List["Role"]] = relationship(
        secondary="user_role_link",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Role(Base):
    """Роль (набор разрешений)."""
    __tablename__ = "role"
    __table_args__ = (UniqueConstraint("name", name="uq_role_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    users: Mapped[List["User"]] = relationship(
        secondary="user_role_link",
        back_populates="roles",
        lazy="selectin",
    )

    permissions: Mapped[List["Permission"]] = relationship(
        secondary="role_permission_link",
        back_populates="roles",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class Permission(Base):
    """Право (действие, разрешённое роли)."""
    __tablename__ = "permission"
    __table_args__ = (UniqueConstraint("code", name="uq_permission_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    roles: Mapped[List["Role"]] = relationship(
        secondary="role_permission_link",
        back_populates="permissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"
