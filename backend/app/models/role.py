# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Optional
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Role(Base):
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
