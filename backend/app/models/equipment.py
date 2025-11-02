# -*- coding: utf-8 -*-
"""
Новые производственные сущности:
- Line (производственная линия)
- Machine (машина/единица оборудования)
- Repair (ремонт/обслуживание)
- RepairAttachment (файлы/изображения к ремонту)
Дополнения:
- Готовность к логированию (audit trail)
"""

from __future__ import annotations

import enum
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    Boolean,
    Float,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# ⚠️ Импорт Base — поправь при необходимости (в некоторых проектах он в app.db)
from app.models import Base
from app.models.mixins import BaseModelMixin


# ==============================================================
# ENUM-типы
# ==============================================================

class LineStatus(enum.Enum):
    working = "working"
    maintenance = "maintenance"
    stopped = "stopped"


class MachineStatus(enum.Enum):
    operational = "operational"
    broken = "broken"
    maintenance = "maintenance"


class RepairType(enum.Enum):
    scheduled = "scheduled"
    unscheduled = "unscheduled"


class RepairStatus(enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"


# ==============================================================
# MODELS
# ==============================================================

class Line(Base, BaseModelMixin):
    """Производственная линия, содержит множество машин."""
    __tablename__ = "lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, doc="Уникальный код линии")
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[LineStatus] = mapped_column(
        Enum(LineStatus, name="line_status"),
        nullable=False,
        default=LineStatus.working,
        server_default=LineStatus.working.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # связи
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


class Machine(Base, BaseModelMixin):
    """Машина/единица оборудования."""
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lines.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    asset_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    status: Mapped[MachineStatus] = mapped_column(
        Enum(MachineStatus, name="machine_status"),
        nullable=False,
        default=MachineStatus.operational,
        server_default=MachineStatus.operational.value,
    )

    last_repair_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    hours_since_last_repair: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    # связи
    line: Mapped["Line"] = relationship(back_populates="machines", lazy="joined")
    repairs: Mapped[List["Repair"]] = relationship(
        back_populates="machine",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_machines_line_id", "line_id"),
        Index("ix_machines_status", "status"),
        Index("ix_machines_active", "is_active"),
        Index("ix_machines_asset_number", "asset_number"),
        Index("ix_machines_serial_number", "serial_number"),
    )

    def __repr__(self) -> str:
        return f"<Machine id={self.id} line_id={self.line_id} name={self.name!r}>"


class Repair(Base, BaseModelMixin):
    """Ремонт/обслуживание машины."""
    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    machine_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("machines.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    asset_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actions_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    performed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, doc="Кто выполнял ремонт"
    )
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, doc="Кто создал запись"
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    repair_type: Mapped[RepairType] = mapped_column(
        Enum(RepairType, name="repair_type"),
        nullable=False,
        default=RepairType.unscheduled,
        server_default=RepairType.unscheduled.value,
    )
    status: Mapped[RepairStatus] = mapped_column(
        Enum(RepairStatus, name="repair_status"),
        nullable=False,
        default=RepairStatus.open,
        server_default=RepairStatus.open.value,
    )

    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    parts_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    downtime_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # связи
    machine: Mapped["Machine"] = relationship(back_populates="repairs", lazy="joined")
    attachments: Mapped[List["RepairAttachment"]] = relationship(
        back_populates="repair",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_repairs_machine_id", "machine_id"),
        Index("ix_repairs_status", "status"),
        Index("ix_repairs_type", "repair_type"),
        Index("ix_repairs_asset_number", "asset_number"),
        Index("ix_repairs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Repair id={self.id} machine_id={self.machine_id} status={self.status.value}>"


class RepairAttachment(Base, BaseModelMixin):
    """Файлы и изображения, прикреплённые к ремонтной записи."""
    __tablename__ = "repair_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repair_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    original_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False, doc="Путь к файлу/объекту")
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # связи
    repair: Mapped["Repair"] = relationship(back_populates="attachments", lazy="joined")

    __table_args__ = (
        Index("ix_repair_attachments_repair_id", "repair_id"),
    )

    def __repr__(self) -> str:
        return f"<RepairAttachment id={self.id} repair_id={self.repair_id} name={self.original_name!r}>"
