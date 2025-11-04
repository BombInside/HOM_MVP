# -*- coding: utf-8 -*-
"""
Точка входа FastAPI: CORS, middleware, аудит, роутеры и lifecycle.
Исправлен порядок инициализации, убрано авто-создание таблиц.
"""

from __future__ import annotations
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.db import wait_for_db_ready
from app.admin_panel import router as admin_router
from app.routes_auth import router as auth_router
from app.api.system import router as system_router

# Роутеры домена и аудит
from app.api.equipment import lines, machines, repairs, repair_attachments
from app.api import audit_log
from app.middleware.audit_middleware import AuditUserMiddleware
from app.models import Base
#from app.core.audit_listeners import attach_audit_events 

logger = logging.getLogger(__name__)
settings = get_settings()

# ==========================================================
# Инициализация приложения
# ==========================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=getattr(settings, "VERSION", "1.0.0"),
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ==========================================================
# Middleware и системные настройки
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=(settings.JWT_SECRET or "insecure"))
app.add_middleware(AuditUserMiddleware)

# Подключаем аудит изменений
#attach_audit_events(Base)

# ==========================================================
# Роутеры
# ==========================================================

# Системные и базовые
app.include_router(auth_router)             # /auth/*
app.include_router(admin_router)            # /adminpanel/*
app.include_router(system_router)           # /health/*

# Доменные
app.include_router(lines.router, prefix="/api")                 # type: ignore[attr-defined]
app.include_router(machines.router, prefix="/api")              # type: ignore[attr-defined]
app.include_router(repairs.router, prefix="/api")               # type: ignore[attr-defined]
app.include_router(repair_attachments.router, prefix="/api")   # type: ignore[attr-defined]

# Аудит
app.include_router(audit_log.router, prefix="/api")             # type: ignore[attr-defined]


# ==========================================================
# События приложения
# ==========================================================

@app.on_event("startup")
async def on_startup() -> None:
    """Ожидание готовности БД и Alembic-инициализация (если нужно)."""
    await wait_for_db_ready()
    logger.info("✅ Database connection established.")
    logger.info("🚀 Application startup complete.")


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Корневой эндпоинт."""
    return {"app": settings.APP_NAME, "env": getattr(settings, "APP_ENV", "stage")}
