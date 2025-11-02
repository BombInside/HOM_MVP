# -*- coding: utf-8 -*-
"""
Общие миксины для ORM-моделей.
Добавляют временные метки, soft delete и аудит действий пользователя.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

class BaseModelMixin:
    """Добавляет стандартные поля: created_at, updated_at, deleted_at, deleted_by."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    deleted_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    def soft_delete(self, user_id: Optional[int] = None):
        """Помечает запись как удалённую (soft delete)."""
        self.deleted_at = datetime.utcnow()
        if user_id:
            self.deleted_by = user_id
