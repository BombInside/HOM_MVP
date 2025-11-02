# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, List
from sqlalchemy import String, Text, Enum, Boolean, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base
from app.models.mixins import BaseModelMixin
from .enums import LineStatus


class Line(Base, BaseModelMixin):
    """
    Производственная линия.
    """
    __tablename__ = "lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Исправлено: добавлен create_type=False для предотвращения повторного создания ENUM
    status: Mapped[LineStatus] = mapped_column(
        Enum(LineStatus, name="line_status", create_type=False, native_enum=True),
        nullable=False,
        default=LineStatus.working,
        server_default=LineStatus.working.value,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    notes: Mapped[Optional[str]] = mapped_column(Text)

    machines: Mapped[List["Machine"]] = relationship(
        back_populates="line",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_lines_code", "code", unique=True),
        Index("ix_lines_is_active", "is_active"),
        Index("ix_lines_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Line id={self.id} code={self.code!r} name={self.name!r}>"
