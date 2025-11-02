# -*- coding: utf-8 -*-
"""
API для управления машинами (Machine)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.schemas.machine import MachineCreate, MachineUpdate, MachineOut
from app.services.machines import machine_service

router = APIRouter(prefix="/machines", tags=["Machines"])


@router.post("/", response_model=MachineOut)
async def create_machine(
    data: MachineCreate,
    db: AsyncSession = Depends(get_session),
):
    """
    Создание новой машины
    """
    return await machine_service.create(db, data)


@router.get("/", response_model=list[MachineOut])
async def list_machines(
    db: AsyncSession = Depends(get_session),
):
    """
    Получить список всех машин (только активных)
    """
    return await machine_service.list(db)


@router.get("/{machine_id}", response_model=MachineOut)
async def get_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    Получить машину по ID
    """
    return await machine_service.get_or_404(db, machine_id)


@router.patch("/{machine_id}", response_model=MachineOut)
async def update_machine(
    machine_id: int,
    data: MachineUpdate,
    db: AsyncSession = Depends(get_session),
):
    """
    Обновить информацию о машине
    """
    return await machine_service.update(db, machine_id, data)


@router.delete("/{machine_id}")
async def delete_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    Мягкое удаление машины (soft delete)
    """
    await machine_service.soft_delete(db, machine_id)
    return {"message": "Machine soft-deleted"}
