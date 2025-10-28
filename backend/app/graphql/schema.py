import strawberry
from typing import List, Optional 
# EN: Added HTTPException for auth checks
# RU: Добавлен HTTPException для проверок аутентификации
from fastapi import Depends, HTTPException
from datetime import datetime 
from strawberry.fastapi import GraphQLRouter
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
# EN: Added BaseModel and field_validator from Pydantic for DTOs and validation
# RU: Добавлены BaseModel и field_validator из Pydantic для DTO и валидации
from pydantic import BaseModel, field_validator 
from ..db import async_session
from ..models import Line, Machine, AuditLog, User, Repair
# EN: Import the new dependency for getting the current authenticated user
# RU: Импортируем новую зависимость для получения текущего аутентифицированного пользователя
from ..auth import get_current_user 

async def get_session() -> AsyncSession:
    async with async_session() as s:
        yield s

# ----------------------------------------------------
# EN: Context getter updated to use real authentication (SECURITY FIX)
# RU: Context getter обновлен для использования реальной аутентификации (ИСПРАВЛЕНИЕ БЕЗОПАСНОСТИ)
# ----------------------------------------------------
# EN: current_user is provided by the JWT dependency
# RU: current_user предоставляется JWT зависимостью
def get_context(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # EN: The real authenticated user is now passed to the context
    # RU: Реальный аутентифицированный пользователь теперь передается в контекст
    return {"session": session, "user": current_user} 

# ----------------------------------------------------
# EN: Input Model for Repair Creation (DTO with Validation)
# RU: Модель Входных Данных для Создания Ремонта (DTO с Валидацией)
# ----------------------------------------------------
class RepairCreateInput(BaseModel):
    machine_id: int
    title: str
    description: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    # EN: Business logic validation: finished time must be after start time
    # RU: Валидация бизнес-логики: время окончания должно быть строго после времени начала
    @field_validator('finished_at')
    @classmethod
    def validate_dates(cls, v, info):
        if info.data.get('started_at') and v and v <= info.data['started_at']:
            # EN: Raise validation error if finish time is not logical
            # RU: Вызываем ошибку валидации, если время окончания нелогично
            raise ValueError('Finished time must be strictly after started time.')
        return v

# --------------------
# EN: GraphQL Types
# --------------------

@strawberry.type
class LineType:
    id: int
    name: str
    is_deleted: bool 
    
@strawberry.type
class MachineType:
    id: int
    asset: str
    line_id: int
    is_deleted: bool 
    
@strawberry.type
class RepairType:
    id: int
    machine_id: int
    title: str
    description: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    created_by: int
    is_deleted: bool # EN: Added soft delete flag

# --------------------
# EN: GraphQL Queries (Requires Authentication)
# --------------------

@strawberry.type
class Query:
    @strawberry.field
    async def lines(self, info) -> List[LineType]:
        # EN: Authentication is now implicitly required by the context_getter
        # RU: Аутентификация теперь неявно требуется через context_getter
        session: AsyncSession = info.context["session"]
        
        # EN: Only select active (non-deleted) lines
        # RU: Выбираем только активные (не удаленные) линии
        res = await session.execute(select(Line).where(Line.is_deleted == False))
        return [LineType(id=l.id, name=l.name, is_deleted=l.is_deleted) for l in res.scalars().all()]

    @strawberry.field
    async def machines(self, info) -> List[MachineType]:
        session: AsyncSession = info.context["session"]
        # EN: Only select active (non-deleted) machines
        # RU: Выбираем только активные (не удаленные) станки
        res = await session.execute(select(Machine).where(Machine.is_deleted == False))
        return [MachineType(id=m.id, asset=m.asset, line_id=m.line_id, is_deleted=m.is_deleted) for m in res.scalars().all()]

# --------------------
# EN: GraphQL Mutations (Core MVP Functionality)
# --------------------

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_line(self, info, name: str) -> LineType:
        session: AsyncSession = info.context["session"]
        user: User = info.context["user"] # EN: User is guaranteed to exist now (from context)
        
        # ⚠️ EN: RBAC CHECK (Future implementation needed, e.g., only Admins can create lines)
        # ⚠️ RU: ПРОВЕРКА RBAC (Требуется будущая реализация, например, только Админы могут создавать линии)
             
        # EN: Core Business Logic: Create new Line
        # RU: Основная Бизнес-логика: Создание новой линии
        new_line = Line(name=name)
        session.add(new_line)
        await session.commit()
        await session.refresh(new_line)

        # 💡 EN: AUDIT LOGGING: Record the creation event
        # 💡 RU: ЛОГИРОВАНИЕ АУДИТА: Записываем событие создания
        audit = AuditLog(
            entity="Line",
            entity_id=str(new_line.id),
            action="CREATE",
            performed_by=user.id,
            diff={"name": name}
        )
        session.add(audit)
        await session.commit()
        
        return LineType(id=new_line.id, name=new_line.name, is_deleted=new_line.is_deleted)

    @strawberry.mutation
    async def create_repair(self, info, data: RepairCreateInput) -> RepairType:
        session: AsyncSession = info.context["session"]
        user: User = info.context["user"] # EN: User is guaranteed to exist now (from context)

        # ⚠️ EN: RBAC CHECK (Future implementation needed, e.g., only Technicians can create repairs)
        # ⚠️ RU: ПРОВЕРКА RBAC (Требуется будущая реализация, например, только Техники могут создавать ремонты)
        
        # EN: Core Business Logic: Create new Repair
        # RU: Основная Бизнес-логика: Создание нового Ремонта
        new_repair = Repair(
            **data.model_dump(), # EN: Use Pydantic's method to convert to dict
            created_by=user.id
        )
        
        session.add(new_repair)
        await session.commit()
        await session.refresh(new_repair)

        # 💡 EN: AUDIT LOGGING
        # 💡 RU: ЛОГИРОВАНИЕ АУДИТА
        audit = AuditLog(
            entity="Repair",
            entity_id=str(new_repair.id),
            action="CREATE",
            performed_by=user.id,
            diff=data.model_dump()
        )
        session.add(audit)
        await session.commit()
        
        return RepairType(**new_repair.model_dump())

# --------------------
# EN: Final Schema setup
# --------------------
schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQLRouter(schema, context_getter=get_context)