# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, List
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Permission(Base):
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
