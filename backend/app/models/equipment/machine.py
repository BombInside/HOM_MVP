# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import date
from typing import Optional, List
from sqlalchemy import String, Text, Enum, Boolean, Integer, Date, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base
from app.models.mixins import BaseModelMixin
from .enums import MachineStatus

class Machine(Base, BaseModelMixin):
    __tablename__ = "machines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    line_id: Mapped[int] = mapped_column(Integer, ForeignKey("lines.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    asset_number: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(128))
    model: Mapped[Optional[str]] = mapped_column(String(128))
    type: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[MachineStatus] = mapped_column(
        Enum(MachineStatus, name="machine_status", create_type=False),
        nullable=False,
        default=MachineStatus.operational,
        server_default=MachineStatus.operational.value,
    )
    last_repair_date: Mapped[Optional[date]] = mapped_column(Date)
    hours_since_last_repair: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    line: Mapped["Line"] = relationship(back_populates="machines", lazy="joined")
    repairs: Mapped[List["Repair"]] = relationship(back_populates="machine", lazy="selectin")

    __table_args__ = (
        Index("ix_machines_line_id", "line_id"),
        Index("ix_machines_status", "status"),
        Index("ix_machines_active", "is_active"),
        Index("ix_machines_asset_number", "asset_number"),
        Index("ix_machines_serial_number", "serial_number"),
    )

    def __repr__(self) -> str:
        return f"<Machine id={self.id} line_id={self.line_id} name={self.name!r}>"
