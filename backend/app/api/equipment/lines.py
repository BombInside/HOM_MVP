from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.schemas.line import LineCreate, LineUpdate, LineOut
from app.services.lines import line_service

router = APIRouter(prefix="/lines", tags=["Lines"])

@router.post("/", response_model=LineOut)
async def create_line(data: LineCreate, db: AsyncSession = Depends(get_session)):
    return await line_service.create(db, data)

@router.get("/", response_model=list[LineOut])
async def list_lines(db: AsyncSession = Depends(get_session)):
    return await line_service.list(db)

@router.get("/{line_id}", response_model=LineOut)
async def get_line(line_id: int, db: AsyncSession = Depends(get_session)):
    return await line_service.get_or_404(db, line_id)

@router.patch("/{line_id}", response_model=LineOut)
async def update_line(line_id: int, data: LineUpdate, db: AsyncSession = Depends(get_session)):
    return await line_service.update(db, line_id, data)

@router.delete("/{line_id}")
async def delete_line(line_id: int, db: AsyncSession = Depends(get_session)):
    await line_service.soft_delete(db, line_id)
    return {"message": "Line soft-deleted"}
