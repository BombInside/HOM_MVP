# -*- coding: utf-8 -*-
"""
Сервис для получения записей из audit_log
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
from typing import List, Optional
from app.models.audit_log import AuditLog


class AuditLogService:
    """Предоставляет методы фильтрации и выборки аудита."""

    async def list(
        self,
        db: AsyncSession,
        table_name: Optional[str] = None,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AuditLog]:
        stmt = select(AuditLog)

        # фильтрация
        conditions = []
        if table_name:
            conditions.append(AuditLog.table_name == table_name)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)
        if from_date:
            conditions.append(AuditLog.timestamp >= from_date)
        if to_date:
            conditions.append(AuditLog.timestamp <= to_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, db: AsyncSession, log_id: int) -> Optional[AuditLog]:
        return await db.get(AuditLog, log_id)


audit_log_service = AuditLogService()
