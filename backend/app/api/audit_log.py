# -*- coding: utf-8 -*-
"""
API для просмотра истории изменений (Audit Log)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional, List

from app.db import get_session
from app.schemas.audit_log import AuditLogOut
from app.services.audit_log import audit_log_service

router = APIRouter(prefix="/audit-log", tags=["AuditLog"])


@router.get("/", response_model=List[AuditLogOut])
async def list_audit_logs(
    db: AsyncSession = Depends(get_session),
    table_name: Optional[str] = Query(None, description="Название таблицы"),
    user_id: Optional[int] = Query(None, description="ID пользователя"),
    action: Optional[str] = Query(None, description="CREATE / UPDATE / DELETE"),
    from_date: Optional[datetime] = Query(None, description="С даты"),
    to_date: Optional[datetime] = Query(None, description="По дату"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=500),
):
    """
    Получить список изменений с фильтрацией.
    """
    logs = await audit_log_service.list(
        db=db,
        table_name=table_name,
        user_id=user_id,
        action=action,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )
    return logs


@router.get("/{log_id}", response_model=AuditLogOut)
async def get_audit_log(log_id: int, db: AsyncSession = Depends(get_session)):
    """
    Получить подробную информацию об одном изменении.
    """
    log = await audit_log_service.get_by_id(db, log_id)
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log
