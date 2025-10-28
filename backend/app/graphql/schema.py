import strawberry
from typing import List
from fastapi import Depends, HTTPException # EN: Added HTTPException for auth checks
from strawberry.fastapi import GraphQLRouter
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import async_session
from ..models import Line, Machine, AuditLog, User # EN: Added AuditLog, User

async def get_session() -> AsyncSession:
    async with async_session() as s:
        yield s

# 💡 EN: Context getter must be extended to securely get the authenticated user later
# 💡 RU: Context getter должен быть расширен для безопасного получения аутентифицированного пользователя
def get_context(session: AsyncSession = Depends(get_session)):
    # EN: The 'user' field should be populated by an Auth Dependency based on JWT
    # RU: Поле 'user' должно заполняться Auth Dependency на основе JWT
    return {"session": session, "user": User(id=1, email="system@hom.local", hashed_password="mock")} # Mock user for now

# --------------------
# EN: GraphQL Types
# --------------------

@strawberry.type
class LineType:
    id: int
    name: str
    is_deleted: bool # EN: Added soft delete flag
    
@strawberry.type
class MachineType:
    id: int
    asset: str
    line_id: int
    is_deleted: bool # EN: Added soft delete flag

# --------------------
# EN: GraphQL Queries
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
# EN: GraphQL Mutations (Core MVP Functionality)
# --------------------

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_line(self, info, name: str) -> LineType:
        session: AsyncSession = info.context["session"]
        
        # ⚠️ EN: AUTH CHECK (To be fully implemented in Phase 1)
        # ⚠️ RU: ПРОВЕРКА АУТЕНТИФИКАЦИИ (Будет полностью реализовано в Фазе 1)
        user: User = info.context.get("user")
        if not user:
             # EN: Use 401/403 errors for authentication/authorization
             # RU: Используем 401/403 для ошибок аутентификации/авторизации
             raise HTTPException(status_code=401, detail="Authentication required.")
             
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

# --------------------
# EN: Final Schema setup
# --------------------
schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQLRouter(schema, context_getter=get_context)