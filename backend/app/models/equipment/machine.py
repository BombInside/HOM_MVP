# app/models/equipment/machine.py
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.equipment.enums import MachineStatus


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    line_id: Mapped[int] = mapped_column(sa.ForeignKey("lines.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    serial_number: Mapped[str] = mapped_column(sa.String(100), nullable=False, index=True)
    status: Mapped[MachineStatus] = mapped_column(
        sa.Enum(MachineStatus, name="machine_status", create_type=False, native_enum=True),
        nullable=False,
        default=MachineStatus.operational,
    )

    line: Mapped["Line"] = relationship("Line", back_populates="machines")
    repairs: Mapped[list["Repair"]] = relationship("Repair", back_populates="machine", cascade="all,delete-orphan")

    __table_args__ = (
        sa.UniqueConstraint("serial_number", name="uq_machines_serial_number"),
    )
