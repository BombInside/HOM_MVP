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

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GraphQL ---
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
async def health(session: AsyncSession = Depends(get_session)):
    """
    Проверка состояния Postgres, Redis и окружения.
    Возвращает:
      - status: общий статус
      - db_status: ok/error
      - redis_status: ok/error
      - env: stage/dev/prod
    """
    # Проверка базы
    db_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    # Проверка Redis
    redis_status = "ok"
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        pong = await r.ping()
        if not pong:
            redis_status = "error"
    except Exception:
        redis_status = "error"
    finally:
        await r.aclose()

    # Общий статус
    status = "ok" if db_status == "ok" and redis_status == "ok" else "error"

    return {
        "status": status,
        "db_status": db_status,
        "redis_status": redis_status,
        "env": settings.APP_ENV,
    }


@app.get("/redis-health")
async def redis_health():
    """Оставлен для совместимости (можно удалить позже)."""
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        pong = await r.ping()
        return {"status": "ok" if pong else "offline"}
    except Exception:
        return {"status": "error"}
    finally:
        await r.aclose()
