# -*- coding: utf-8 -*-
"""
Системные эндпоинты (health-check сервисов).
Возвращает статусы backend / database / redis.
"""
from __future__ import annotations
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db import get_session

# redis 5.x поддерживает asyncio-клиент в redis.asyncio
from redis.asyncio import Redis

router = APIRouter(prefix="/health", tags=["system"])


async def check_db(session: AsyncSession) -> str:
    """Быстрая проверка подключения к БД."""
    try:
        await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "fail"


async def check_redis() -> str:
    """Быстрая проверка доступности Redis."""
    # Хост 'redis' — имя сервиса в docker-compose
    client = Redis(host="redis", port=6379, db=0)
    try:
        pong = await client.ping()
        return "ok" if pong else "fail"
    except Exception:
        return "fail"
    finally:
        # Закрываем соединение корректно
        try:
            await client.aclose()
        except Exception:
            pass


@router.get("/", summary="Проверка статусов сервисов")
async def health(session: AsyncSession = Depends(get_session)) -> Dict[str, str]:
    """
    Возвращает статусы основных сервисов.
    Ответ:
    {
      "backend": "ok|fail",
      "database": "ok|fail",
      "redis": "ok|fail"
    }
    """
    db_status = await check_db(session)
    redis_status = await check_redis()
    return {"backend": "ok", "database": db_status, "redis": redis_status}
