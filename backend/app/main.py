# -*- coding: utf-8 -*-
"""
Точка входа FastAPI: монтируем админ-панель, аутентификацию, настраиваем CORS и логирование.
"""
from __future__ import annotations
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from .db import wait_for_db_ready, create_db_and_tables
from .admin_panel import router as admin_router
from .routes_auth import router as auth_router

# ✅ Новый системный роутер /health
from .api.system import router as system_router

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Сессии (если используются шаблоны/админка)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)

# Роуты
app.include_router(auth_router)     # /auth/*
app.include_router(admin_router)    # /adminpanel/*
app.include_router(system_router)   # /health/*

@app.on_event("startup")
async def on_startup() -> None:
    """Ожидание готовности БД (минимальная защита от гонки) и создание таблиц."""
    await wait_for_db_ready()
    await create_db_and_tables()
    logger.info("Application started.")

@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Простой корневой эндпоинт."""
    return {"app": settings.APP_NAME, "env": settings.ENV}
