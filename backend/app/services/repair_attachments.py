# -*- coding: utf-8 -*-
"""
Сервисный слой для управления файлами ремонта (RepairAttachment).
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.equipment import Repair, RepairAttachment


class RepairAttachmentService:
    """Логика работы с файлами ремонтов."""

    def __init__(self, db: AsyncSession, upload_dir: str = "uploads/repairs"):
        self.db = db
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    async def get_all(self, repair_id: int) -> list[RepairAttachment]:
        stmt = select(RepairAttachment).where(RepairAttachment.repair_id == repair_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get(self, attachment_id: int) -> RepairAttachment:
        attach = await self.db.get(RepairAttachment, attachment_id)
        if not attach:
            raise HTTPException(status_code=404, detail="Attachment not found")
        return attach

    async def upload_file(
        self,
        repair_id: int,
        file: UploadFile,
        uploaded_by: Optional[int] = None,
    ) -> RepairAttachment:
        """Загрузка файла и создание записи в БД."""

        repair = await self.db.get(Repair, repair_id)
        if not repair:
            raise HTTPException(status_code=404, detail="Repair not found")

        filename = f"{repair_id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
        filepath = os.path.join(self.upload_dir, filename)

        # сохраняем файл
        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())

        attach = RepairAttachment(
            repair_id=repair_id,
            original_name=file.filename,
            file_path=filepath,
            mime_type=file.content_type,
            size_bytes=os.path.getsize(filepath),
            uploaded_by=uploaded_by,
            created_at=datetime.utcnow(),
        )

        self.db.add(attach)
        await self.db.commit()
        await self.db.refresh(attach)
        return attach

    async def delete(self, attachment_id: int) -> None:
        """Удаление файла и записи."""
        attach = await self.db.get(RepairAttachment, attachment_id)
        if not attach:
            raise HTTPException(status_code=404, detail="Attachment not found")

        # Удаляем физический файл, если он существует
        if attach.file_path and os.path.exists(attach.file_path):
            os.remove(attach.file_path)

        await self.db.delete(attach)
        await self.db.commit()
