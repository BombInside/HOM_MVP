# -*- coding: utf-8 -*-
"""
Точка входа FastAPI: монтируем админ-панель, настраиваем CORS и логирование в JSON.
"""
from __future__ import annotations
import logging
import json as _json
from typing import List
from fastapi import FastAPI
from app.api.adminpanel import routes_bootstrap
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from .db import wait_for_db_ready, create_db_and_tables
from .admin_panel import router as admin_router

settings = get_settings()
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)


app.include_router(routes_bootstrap.router, prefix=\"/adminpanel\", tags=[\"AdminPanel\"])
class JsonFormatter(logging.Formatter):
    """Простой JSON-форматтер логов для продакшена."""
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return _json.dumps(payload, ensure_ascii=False)


# Логирование
root = logging.getLogger()
if settings.LOG_JSON:
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Сессии (секрет должен приходить из JWT_SECRET: это нормально для MVP)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)


# Роуты
app.include_router(admin_router)


@app.on_event("startup")
async def on_startup() -> None:
    await wait_for_db_ready()
    await create_db_and_tables()


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"app": settings.APP_NAME, "env": settings.ENV}
