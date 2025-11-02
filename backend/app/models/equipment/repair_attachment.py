# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base
from app.models.mixins import BaseModelMixin

class RepairAttachment(Base, BaseModelMixin):
    __tablename__ = "repair_attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repair_id: Mapped[int] = mapped_column(Integer, ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False, index=True)
    original_name: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128))
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    uploaded_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    repair: Mapped["Repair"] = relationship(back_populates="attachments", lazy="joined")
    __table_args__ = (Index("ix_repair_attachments_repair_id", "repair_id"),)
    def __repr__(self) -> str:
        return f"<RepairAttachment id={self.id} repair_id={self.repair_id} name={self.original_name!r}>"
