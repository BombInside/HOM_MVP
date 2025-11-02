# -*- coding: utf-8 -*-
"""
Сервисный слой для управления файлами ремонта (RepairAttachment).
Поддерживает загрузку, получение и удаление вложений.

Особенности:
- Интегрирован с CRUDServiceBase (для soft-delete и стандартных CRUD операций)
- Готов к добавлению аудита и BaseModelMixin
- Расширяем для подключения S3/MinIO в будущем
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, List

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.equipment import Repair, RepairAttachment
from app.services.base import CRUDServiceBase


class RepairAttachmentService(CRUDServiceBase[RepairAttachment, dict, dict]):
    """Сервис для управления файлами ремонтных записей."""

    def __init__(self, model=RepairAttachment, upload_dir: str = "uploads/repairs"):
        super().__init__(model)
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    # -------------------------
    # Получение всех вложений
    # -------------------------
    async def get_all(self, db: AsyncSession, repair_id: int) -> List[RepairAttachment]:
        stmt = select(RepairAttachment).where(RepairAttachment.repair_id == repair_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    # -------------------------
    # Загрузка нового файла
    # -------------------------
    async def upload_file(
        self,
        db: AsyncSession,
        repair_id: int,
        file: UploadFile,
        uploaded_by: Optional[int] = None,
    ) -> RepairAttachment:
        """Загрузка файла и создание записи в БД."""
        repair = await db.get(Repair, repair_id)
        if not repair:
            raise HTTPException(status_code=404, detail="Repair not found")

        filename = f"{repair_id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
        filepath = os.path.join(self.upload_dir, filename)

        # сохраняем файл на диск
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

        db.add(attach)
        await db.commit()
        await db.refresh(attach)
        return attach

    # -------------------------
    # Удаление файла (жёсткое)
    # -------------------------
    async def delete_file(self, db: AsyncSession, attachment_id: int) -> None:
        """Удаляет запись и сам файл с диска."""
        attach = await db.get(RepairAttachment, attachment_id)
        if not attach:
            raise HTTPException(status_code=404, detail="Attachment not found")

        if attach.file_path and os.path.exists(attach.file_path):
            os.remove(attach.file_path)

        await db.delete(attach)
        await db.commit()

    # -------------------------
    # Soft delete (для будущего аудита)
    # -------------------------
    async def soft_delete_file(self, db: AsyncSession, attachment_id: int, deleted_by: Optional[int] = None) -> None:
        """Помечает файл как удалённый без физического удаления (готово для аудита)."""
        attach = await db.get(RepairAttachment, attachment_id)
        if not attach:
            raise HTTPException(status_code=404, detail="Attachment not found")

        if hasattr(attach, "deleted_at"):
            attach.deleted_at = datetime.utcnow()
        if hasattr(attach, "deleted_by") and deleted_by:
            attach.deleted_by = deleted_by

        await db.commit()


# экземпляр сервиса
repair_attachment_service = RepairAttachmentService()
