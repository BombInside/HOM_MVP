import strawberry
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from datetime import datetime
from strawberry.fastapi import GraphQLRouter
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
import functools

from ..db import async_session
from ..models import Line, Machine, AuditLog, User, Repair
from ..auth import get_current_user, has_role


# ==============================================================
# ASYNC SESSION
# ==============================================================

async def get_session() -> AsyncSession:
    async with async_session() as s:
        yield s


# ==============================================================
# CONTEXT (Session + Authenticated User)
# ==============================================================

def get_context(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """GraphQL context: includes DB session and authenticated user"""
    return {"session": session, "user": current_user}


# ==============================================================
# RBAC DECORATOR
# ==============================================================

def requires_role_graphql(required_role_name: str):
    """Decorator for Strawberry GraphQL resolvers with role check"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, info: strawberry.types.Info, **kwargs):
            user: User = info.context.get("user")

            if not user or not has_role(user, required_role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Requires role: {required_role_name}"
                )

            return await func(*args, info=info, **kwargs)
        return wrapper
    return decorator


# ==============================================================
# GRAPHQL INPUT TYPES
# ==============================================================

@strawberry.input
class RepairCreateInput:
    machine_id: int
    title: str
    description: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    @classmethod
    def validate(cls, data: "RepairCreateInput"):
        """Business validation: finished_at must be after started_at"""
        if data.finished_at and data.finished_at <= data.started_at:
            raise ValueError("Finished time must be strictly after started time.")
        return data


# ==============================================================
# GRAPHQL OUTPUT TYPES
# ==============================================================

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


# ==============================================================
# GRAPHQL QUERIES
# ==============================================================

@strawberry.type
class Query:
    @strawberry.field
    async def lines(self, info) -> List[LineType]:
        session: AsyncSession = info.context["session"]
        res = await session.execute(select(Line).where(Line.is_deleted == False))
        return [LineType(id=l.id, name=l.name, is_deleted=l.is_deleted) for l in res.scalars().all()]

    @strawberry.field
    async def machines(self, info) -> List[MachineType]:
        session: AsyncSession = info.context["session"]
        res = await session.execute(select(Machine).where(Machine.is_deleted == False))
        return [MachineType(id=m.id, asset=m.asset, line_id=m.line_id, is_deleted=m.is_deleted) for m in res.scalars().all()]


# ==============================================================
# GRAPHQL MUTATIONS (RBAC-PROTECTED)
# ==============================================================

@strawberry.type
class Mutation:
    @strawberry.mutation
    @requires_role_graphql("Admin")
    async def create_line(self, info, name: str) -> LineType:
        session: AsyncSession = info.context["session"]
        user: User = info.context["user"]

        new_line = Line(name=name)
        session.add(new_line)
        await session.commit()
        await session.refresh(new_line)

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
    @requires_role_graphql("Technician")
    async def create_repair(self, info, data: RepairCreateInput) -> RepairType:
        session: AsyncSession = info.context["session"]
        user: User = info.context["user"]

        # Validate business rule
        RepairCreateInput.validate(data)

        new_repair = Repair(
            machine_id=data.machine_id,
            title=data.title,
            description=data.description,
            started_at=data.started_at,
            finished_at=data.finished_at,
            created_by=user.id,
        )
        session.add(new_repair)
        await session.commit()
        await session.refresh(new_repair)

        audit = AuditLog(
            entity="Repair",
            entity_id=str(new_repair.id),
            action="CREATE",
            performed_by=user.id,
            diff={
                "machine_id": data.machine_id,
                "title": data.title,
                "description": data.description,
                "started_at": str(data.started_at),
                "finished_at": str(data.finished_at),
            },
        )
        session.add(audit)
        await session.commit()

        return RepairType(**new_repair.model_dump())


# ==============================================================
# FINAL SCHEMA SETUP
# ==============================================================

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
