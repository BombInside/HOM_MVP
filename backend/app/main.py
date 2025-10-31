from typing import Any, Coroutine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings

# --- безопасный импорт create_db_and_tables ---
try:
    from app.db import create_db_and_tables
except ImportError:
    async def create_db_and_tables() -> Coroutine[Any, Any, None]:
        """
        Заглушка для create_db_and_tables, если модуль app.db недоступен.
        Используется для корректной проверки типов (mypy).
        """
        return None

from app.graphql.schema import graphql_app
from app.admin_panel import router as admin_router

app = FastAPI(title="H.O.M Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Сессии
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)

# Подключаем маршруты
app.include_router(graphql_app, prefix="/graphql")
app.include_router(admin_router)

@app.on_event("startup")
async def startup() -> None:
    """Создание таблиц и подготовка базы данных при запуске приложения."""
    await create_db_and_tables()

@app.get("/health")
async def health() -> dict[str, str]:
    """Эндпоинт для проверки состояния приложения."""
    return {"status": "ok"}
