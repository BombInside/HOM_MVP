# -*- coding: utf-8 -*-
"""
Базовый CRUD-сервис.

"""

from __future__ import annotations
from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException

from datetime import datetime

ModelType = TypeVar("ModelType")  # SQLAlchemy модель
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class CRUDServiceBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый универсальный CRUD-сервис."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    # -------------------------
    # CREATE
    # -------------------------
    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        obj_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else dict(obj_in)
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # -------------------------
    # READ
    # -------------------------
    async def get(self, db: AsyncSession, obj_id: int) -> Optional[ModelType]:
        result = await db.get(self.model, obj_id)
        if result and getattr(result, "deleted_at", None):
            return None
        return result

    async def get_or_404(self, db: AsyncSession, obj_id: int) -> ModelType:
        obj = await self.get(db, obj_id)
        if not obj:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found")
        return obj

    async def list(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        stmt = select(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        result = await db.execute(stmt.offset(skip).limit(limit))
        return result.scalars().all()

    # -------------------------
    # UPDATE
    # -------------------------
    async def update(self, db: AsyncSession, obj_id: int, obj_in: UpdateSchemaType) -> ModelType:
        db_obj = await self.get_or_404(db, obj_id)
        data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else dict(obj_in)
        for field, value in data.items():
            setattr(db_obj, field, value)
        if hasattr(db_obj, "updated_at"):
            setattr(db_obj, "updated_at", datetime.utcnow())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # -------------------------
    # DELETE (soft or hard)
    # -------------------------
    async def soft_delete(self, db: AsyncSession, obj_id: int, deleted_by: Optional[int] = None) -> None:
        db_obj = await self.get_or_404(db, obj_id)
        if hasattr(db_obj, "deleted_at"):
            db_obj.deleted_at = datetime.utcnow()
        if hasattr(db_obj, "deleted_by") and deleted_by:
            db_obj.deleted_by = deleted_by
        await db.commit()

    async def delete(self, db: AsyncSession, obj_id: int) -> None:
        """Жёсткое удаление"""
        db_obj = await self.get_or_404(db, obj_id)
        await db.delete(db_obj)
        await db.commit()
