from __future__ import annotations

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from .config import settings
from .db import get_session
from .graphql.schema import graphql_app

app = FastAPI(title="H.O.M Backend")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем GraphQL
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health(session: AsyncSession = Depends(get_session)):
    """Проверка состояния Postgres и среды"""
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/redis-health")
async def redis_health():
    """Проверка доступности Redis"""
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        pong = await r.ping()
        return {"status": "ok" if pong else "offline"}
    finally:
        await r.aclose()
