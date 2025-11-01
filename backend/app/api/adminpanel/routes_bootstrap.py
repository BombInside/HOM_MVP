# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_session
from app.models import User
from app.security import hash_password as get_password_hash

router = APIRouter()

@router.get("/bootstrap/status")
async def bootstrap_status(session: AsyncSession = Depends(get_session)) -> dict:
    admin = await session.scalar(select(User).where(getattr(User, "is_admin", False) == True))  # type: ignore[arg-type]
    return {"admin_exists": admin is not None}

@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
async def create_admin(payload: dict, session: AsyncSession = Depends(get_session)) -> dict:
    existing = await session.scalar(select(User).where(getattr(User, "is_admin", False) == True))  # type: ignore[arg-type]
    if existing:
        raise HTTPException(status_code=400, detail="Администратор уже существует")

    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", "")).strip()
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email и пароль обязательны")

    user = User(email=email)
    if hasattr(user, "password_hash"):
        setattr(user, "password_hash", get_password_hash(password))
    elif hasattr(user, "hashed_password"):
        setattr(user, "hashed_password", get_password_hash(password))
    elif hasattr(user, "password"):
        setattr(user, "password", get_password_hash(password))

    if hasattr(user, "is_admin"):
        setattr(user, "is_admin", True)
    if hasattr(user, "is_active"):
        setattr(user, "is_active", True)

    session.add(user)
    await session.commit()
    return {"message": "Администратор успешно создан"}
