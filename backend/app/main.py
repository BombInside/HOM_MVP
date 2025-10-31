from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.db import create_db_and_tables, async_session
from app.graphql.schema import graphql_app
from app.admin_panel import router as admin_router
from app.models import RBACSeed


app = FastAPI(title="H.O.M Backend")

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)

# --- Routers ---
app.include_router(graphql_app, prefix="/graphql")
app.include_router(admin_router)


@app.on_event("startup")
async def startup() -> None:
    """
    Создание таблиц и инициализация RBAC-ролей при первом запуске приложения.
    """
    print("🗄️  Инициализация базы данных...")
    await create_db_and_tables()

    print("🔐 Проверка наличия ролей и разрешений (RBAC seed)...")
    async with async_session() as session:
        await RBACSeed.seed(session)

    print("✅ База данных и роли успешно инициализированы.")


@app.get("/health")
async def health() -> dict[str, str]:
    """Эндпоинт для проверки состояния приложения."""
    return {"status": "ok"}
