# -*- coding: utf-8 -*-
"""
Таблица для хранения истории изменений (audit log).
Автоматически сериализует datetime и другие неподдерживаемые типы в строки.
"""

import json
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import Integer, String, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


def _safe_json(value: Any) -> Any:
    """Рекурсивно преобразует объекты в JSON-совместимый формат."""
    if isinstance(value, dict):
        return {k: _safe_json(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_safe_json(v) for v in value]
    elif isinstance(value, datetime):
        # ISO8601 формат (понятен JS и SQL)
        return value.isoformat()
    else:
        return value


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    object_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    old_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __init__(self, **kwargs):
        """
        Безопасно преобразует old_data/new_data в JSON-пригодный вид.
        Это устраняет ошибку 'Object of type datetime is not JSON serializable'.
        """
        if "old_data" in kwargs and kwargs["old_data"] is not None:
            kwargs["old_data"] = _safe_json(kwargs["old_data"])
        if "new_data" in kwargs and kwargs["new_data"] is not None:
            kwargs["new_data"] = _safe_json(kwargs["new_data"])
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<AuditLog {self.table_name}#{self.object_id} action={self.action}>"
