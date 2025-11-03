# -*- coding: utf-8 -*-
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class UserRoleLink(Base):
    __tablename__ = "user_role_link"
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)

class RolePermissionLink(Base):
    __tablename__ = "role_permission_link"
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True)
