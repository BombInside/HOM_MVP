from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from .config import settings
from .db import get_session
from .graphql.schema import graphql_app

app = FastAPI(title="H.O.M Backend")

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
async def health(session: AsyncSession = get_session.__wrapped__()):  # type: ignore
    # проверка Postgres
    async with get_session() as s:  # корректный контекст для реального вызова
        await s.execute(text("SELECT 1"))

    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/redis-health")
async def redis_health():
    r = redis.from_url("redis://redis:6379", decode_responses=True)
    try:
        pong = await r.ping()
        return {"status": "ok" if pong else "offline"}
    finally:
        await r.aclose()
