# -*- coding: utf-8 -*-
"""
API для управления ремонтами (Repair) — тонкий слой над сервисом.
"""

from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.schemas.repair import RepairCreate, RepairUpdate, RepairOut
from app.services.repairs import repair_service

router = APIRouter(prefix="/repairs", tags=["Repairs"])


@router.post("/", response_model=RepairOut)
async def create_repair(
    data: RepairCreate,
    db: AsyncSession = Depends(get_session),
):
    return await repair_service.create(db, data)


@router.get("/", response_model=list[RepairOut])
async def list_repairs(
    db: AsyncSession = Depends(get_session),
):
    return await repair_service.list(db)


@router.get("/{repair_id}", response_model=RepairOut)
async def get_repair(
    repair_id: int,
    db: AsyncSession = Depends(get_session),
):
    return await repair_service.get_or_404(db, repair_id)


@router.patch("/{repair_id}", response_model=RepairOut)
async def update_repair(
    repair_id: int,
    data: RepairUpdate,
    db: AsyncSession = Depends(get_session),
):
    return await repair_service.update(db, repair_id, data)


@router.delete("/{repair_id}")
async def delete_repair(
    repair_id: int,
    db: AsyncSession = Depends(get_session),
):
    await repair_service.soft_delete(db, repair_id)
    return {"message": "Repair soft-deleted"}
