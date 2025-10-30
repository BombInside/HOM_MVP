import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .db import async_session
from .graphql.schema import graphql_app
from .auth import router as auth_router


# ----------------------------------------------------
# 🧩 Инициализация приложения
# ----------------------------------------------------
app = FastAPI(title="HOM Backend API", version="1.0")

# ----------------------------------------------------
# 🌍 CORS (Frontend <-> Backend)
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # в dev-режиме можно оставить '*'
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------
# ⚙️ Middleware для обработки ошибок (универсальный JSON)
# ----------------------------------------------------
@app.middleware("http")
async def json_error_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ----------------------------------------------------
# 🔌 Health-check endpoints
# ----------------------------------------------------

@app.get("/health")
async def health_check():
    """Проверка, что backend жив"""
    return {"status": "ok", "service": "backend"}


@app.get("/api/ping")
async def api_ping():
    """Проверка REST API"""
    return {"message": "pong"}


@app.get("/db-check")
async def db_check():
    """Проверка соединения с базой данных"""
    try:
        async with async_session() as session:  # type: AsyncSession
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


# ----------------------------------------------------
# 🔐 Auth router (если реализован)
# ----------------------------------------------------
app.include_router(auth_router, prefix="/auth", tags=["Auth"])


# ----------------------------------------------------
# 🔮 GraphQL endpoint
# ----------------------------------------------------
app.mount("/graphql", graphql_app)


# ----------------------------------------------------
# 🏁 Root redirect
# ----------------------------------------------------
@app.get("/")
async def root():
    return {"message": "HOM Backend is running", "graphql": "/graphql"}

# ----------------------------------------------------
# 🧪 Redis health check
# ----------------------------------------------------

@app.get("/redis-health")
async def redis_health():
    try:
        r = redis.from_url("redis://redis:6379", decode_responses=True)
        pong = await r.ping()
        return {"status": "ok" if pong else "offline"}
    except Exception as e:
        return {"status": "offline", "error": str(e)}