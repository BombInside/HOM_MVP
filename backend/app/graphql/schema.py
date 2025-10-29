import strawberry
from typing import List, Optional 
# EN: Added HTTPException and status for auth checks
# RU: Добавлен HTTPException и status для проверок аутентификации
from fastapi import Depends, HTTPException, status 
from datetime import datetime 
from strawberry.fastapi import GraphQLRouter
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
# EN: Added BaseModel and field_validator from Pydantic for DTOs and validation
# RU: Добавлены BaseModel и field_validator из Pydantic для DTO и валидации
from pydantic import BaseModel, field_validator 
from ..db import async_session
from ..models import Line, Machine, AuditLog, User, Repair
# EN: Import the authentication and RBAC helpers
# RU: Импортируем вспомогательные функции аутентификации и RBAC
from ..auth import get_current_user, has_role 

async def get_session() -> AsyncSession:
    async with async_session() as s:
        yield s

# ----------------------------------------------------
# EN: Context getter uses real authentication (SECURITY FIX)
# RU: Context getter использует реальную аутентификацию (ИСПРАВЛЕНИЕ БЕЗОПАСНОСТИ)
# ----------------------------------------------------
def get_context(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # EN: The real authenticated user is now passed to the context
    # RU: Реальный аутентифицированный пользователь теперь передается в контекст
    return {"session": session, "user": current_user} 

# ----------------------------------------------------
# EN: Strawberry Resolver Authorization Decorator (RBAC)
# RU: Декоратор авторизации для резолверов Strawberry (RBAC)
# ----------------------------------------------------
def requires_role_graphql(required_role_name: str):
    def decorator(func):
        async def wrapper(*args, info: strawberry.type.Info, **kwargs):
            user: User = info.context.get("user")
            
            # EN: Check if the user is authenticated and has the required role
            # RU: Проверяем, аутентифицирован ли пользователь и имеет ли требуемую роль
            if not user or not has_role(user, required_role_name):
                # EN: Raise 403 Forbidden
                # RU: Вызываем 403 Forbidden
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail=f"Permission denied. Requires role: {required_role_name}"
                )
            
            # EN: If check passes, execute the original resolver function
            # RU: Если проверка пройдена, выполняем оригинальную функцию резолвера
            return await func(*args, info=info, **kwargs)
        return wrapper
    return decorator


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

    # EN: Business logic validation: finished time must be strictly after start time
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
    is_deleted: bool 

# --------------------
# EN: GraphQL Queries (Protected by context_getter)
# --------------------

@strawberry.type
class Query:
    @strawberry.field
    async def lines(self, info) -> List[LineType]:
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
# EN: GraphQL Mutations (Protected by RBAC)
# --------------------

@strawberry.type
class Mutation:
    @requires_role_graphql("Admin") # <-- RBAC: Только Admin может создавать линии
    @strawberry.mutation
    async def create_line(self, info, name: str) -> LineType:
        session: AsyncSession = info.context["session"]
        user: User = info.context["user"]
             
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

    @requires_role_graphql("Technician") # <-- RBAC: Только Technician может создавать ремонты
    @strawberry.mutation
    async def create_repair(self, info, data: RepairCreateInput) -> RepairType:
        session: AsyncSession = info.context["session"]
        user: User = info.context["user"] 
        
        # EN: Core Business Logic: Create new Repair
        # RU: Основная Бизнес-логика: Создание нового Ремонта
        new_repair = Repair(
            **data.model_dump(), 
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