from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import create_db_and_tables, async_session
from app.models import RBACSeed
from app.graphql.schema import graphql_app
from app.admin_panel import router as admin_router

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
async def startup():
    """Создаёт таблицы и инициализирует RBAC при старте."""
    print("🗄️  Инициализация базы данных...")
    await create_db_and_tables()

    async with async_session() as session:
        try:
            print("🚀 Создание стандартных ролей и разрешений...")
            await RBACSeed.seed(session)
            print("✅ RBAC роли и разрешения успешно созданы.")
        except Exception as e:
            print(f"⚠️ Ошибка при инициализации RBAC: {e}")

    print("✅ Приложение успешно запущено.")


@app.get("/health")
async def health() -> dict[str, str]:
    """Проверка состояния приложения."""
    return {"status": "ok"}
