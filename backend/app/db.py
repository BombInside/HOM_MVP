from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_async_engine(settings.db_url, echo=(settings.app_env=="dev"))
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    pass
