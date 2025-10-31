from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import redis.asyncio as redis

from .error_middleware import json_error_middleware
from .graphql.schema import graphql_app
from .config import get_settings
from .db import get_session

settings = get_settings()

app = FastAPI(title="HOM Backend")

# 🧱 Middleware (глобальная обработка ошибок)
app.middleware("http")(json_error_middleware)

# 🌍 CORS настройка
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔗 GraphQL маршруты
app.include_router(graphql_app, prefix="/graphql")


# 🔥 Health-check endpoints
@app.get("/health")
async def health_check():
    """Проверка доступности backend API"""
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/db-health")
async def db_health(session=Depends(get_session)):
    """Проверка соединения с базой"""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        return {"status": "error"}


@app.get("/redis-health")
async def redis_health():
    """Проверка соединения с Redis"""
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        pong = await r.ping()
        return {"status": "ok" if pong else "offline"}
    except Exception:
        return {"status": "error"}
