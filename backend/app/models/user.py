# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
from typing import List
from sqlalchemy import String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class User(Base):
    __tablename__ = "user"
    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    roles: Mapped[List["Role"]] = relationship(
        secondary="user_role_link",
        back_populates="users",
        lazy="selectin",
    )
    def __repr__(self) -> str:
        return f"<User {self.email}>"
