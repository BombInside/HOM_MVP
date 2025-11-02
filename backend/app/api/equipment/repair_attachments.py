# -*- coding: utf-8 -*-
"""
API для управления вложениями ремонта (RepairAttachment).
"""

from __future__ import annotations
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.services.repair_attachments import repair_attachment_service

router = APIRouter(prefix="/repair-attachments", tags=["RepairAttachments"])


@router.get("/{repair_id}", response_model=list[dict])
async def list_attachments(
    repair_id: int,
    db: AsyncSession = Depends(get_session),
):
    atts = await repair_attachment_service.get_all(db, repair_id)
    return [
        {
            "id": a.id,
            "original_name": a.original_name,
            "file_path": a.file_path,
            "mime_type": a.mime_type,
            "size_bytes": a.size_bytes,
            "uploaded_by": a.uploaded_by,
            "created_at": a.created_at,
        }
        for a in atts
    ]


@router.post("/{repair_id}/upload", response_model=dict)
async def upload_attachment(
    repair_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
):
    a = await repair_attachment_service.upload_file(db, repair_id, file)
    return {
        "id": a.id,
        "original_name": a.original_name,
        "file_path": a.file_path,
        "mime_type": a.mime_type,
        "size_bytes": a.size_bytes,
        "uploaded_by": a.uploaded_by,
        "created_at": a.created_at,
    }


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_session),
):
    await repair_attachment_service.delete_file(db, attachment_id)
    return {"message": "Attachment deleted"}
