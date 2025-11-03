# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Enum, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base
from app.models.mixins import BaseModelMixin
from .enums import RepairType, RepairStatus


class Repair(Base, BaseModelMixin):
    """
    Модель ремонта/обслуживания оборудования.
    """
    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    machine_id: Mapped[int] = mapped_column(Integer, ForeignKey("machines.id", ondelete="RESTRICT"), nullable=False, index=True)
    asset_number: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    description: Mapped[Optional[str]] = mapped_column(Text)
    actions_taken: Mapped[Optional[str]] = mapped_column(Text)

    # Исправлено: теперь ссылается на таблицу "user"
    performed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id", ondelete="SET NULL"))

    # Исправлено: добавлен create_type=False для избежания DuplicateObjectError
    repair_type: Mapped[RepairType] = mapped_column(
        Enum(RepairType, name="repair_type", create_type=False, native_enum=True),
        nullable=False,
        default=RepairType.unscheduled,
        server_default=RepairType.unscheduled.value,
    )
    status: Mapped[RepairStatus] = mapped_column(
        Enum(RepairStatus, name="repair_status", create_type=False, native_enum=True),
        nullable=False,
        default=RepairStatus.open,
        server_default=RepairStatus.open.value,
    )

    cost: Mapped[Optional[float]] = mapped_column(Float)
    parts_used: Mapped[Optional[str]] = mapped_column(Text)
    downtime_hours: Mapped[Optional[float]] = mapped_column(Float)

    machine: Mapped["Machine"] = relationship(back_populates="repairs", lazy="joined")
    attachments: Mapped[List["RepairAttachment"]] = relationship(back_populates="repair", lazy="selectin")

    __table_args__ = (
        Index("ix_repairs_machine_id", "machine_id"),
        Index("ix_repairs_status", "status"),
        Index("ix_repairs_type", "repair_type"),
        Index("ix_repairs_asset_number", "asset_number"),
        Index("ix_repairs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Repair id={self.id} machine_id={self.machine_id} status={self.status.value}>"
