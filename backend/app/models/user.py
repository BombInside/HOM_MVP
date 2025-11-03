# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
from typing import List
from sqlalchemy import String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

from app.security import hash_password, verify_password

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
        back_populates="user",
        lazy="selectin",
    )
    def __repr__(self) -> str:
        return f"<User {self.email}>"
    
    def set_password(self, raw_password: str) -> None:
        self.password_hash = hash_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return verify_password(raw_password, self.password_hash)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} admin={self.is_admin}>"
    
    roles: Mapped[List["Role"]] = relationship(
        secondary="user_role_link",
        back_populates="users",
    )
