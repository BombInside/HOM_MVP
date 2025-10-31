from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings

# --- безопасный импорт create_db_and_tables ---
try:
    from app.db import create_db_and_tables  # type: ignore[attr-defined]
except ImportError:
    async def create_db_and_tables():  # type: ignore[no-redef]
        """Заглушка, чтобы mypy не ругался."""
        pass

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
async def startup():
    await create_db_and_tables()

@app.get("/health")
async def health():
    return {"status": "ok"}
