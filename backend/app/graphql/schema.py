import strawberry
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from datetime import datetime
from strawberry.fastapi import GraphQLRouter
from sqlmodel import select
from sqlalchemy import not_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator

from ..db import async_session
from ..models import Line, Machine, AuditLog, User, Repair
from ..auth import get_current_user, has_role


async def get_session() -> AsyncSession:
    async with async_session() as s:
        yield s


def get_context(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    return {"session": session, "user": current_user}


def requires_role_graphql(required_role_name: str):
    def decorator(func):
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


class RepairCreateInput(BaseModel):
    machine_id: int
    title: str
    description: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    @field_validator('finished_at')
    @classmethod
    def validate_dates(cls, v, info):
        if info.data.get('started_at') and v and v <= info.data['started_at']:
            raise ValueError('Finished time must be strictly after started time.')
        return v


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


@strawberry.type
class Query:
    @strawberry.field
    async def lines(self, info) -> List[LineType]:
        session: AsyncSession = info.context["session"]
        res = await session.execute(select(Line).where(not_(Line.is_deleted)))
        return [
            LineType(id=row.id, name=row.name, is_deleted=row.is_deleted)
            for row in res.scalars().all()
        ]

    @strawberry.field
    async def machines(self, info) -> List[MachineType]:
        session: AsyncSession = info.context["session"]
        res = await session.execute(select(Machine).where(not_(Machine.is_deleted)))
        return [
            MachineType(
                id=row.id, asset=row.asset, line_id=row.line_id, is_deleted=row.is_deleted
            )
            for row in res.scalars().all()
        ]


@strawberry.type
class Mutation:
    @requires_role_graphql("Admin")
    @strawberry.mutation
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
            diff={"name": name},
        )
        session.add(audit)
        await session.commit()

        return LineType(id=new_line.id, name=new_line.name, is_deleted=new_line.is_deleted)

    @requires_role_graphql("Technician")
    @strawberry.mutation
    async def create_repair(self, info, data: RepairCreateInput) -> RepairType:
        session: AsyncSession = info.context["session"]
        user: User = info.context["user"]

        new_repair = Repair(**data.model_dump(), created_by=user.id)
        session.add(new_repair)
        await session.commit()
        await session.refresh(new_repair)

        audit = AuditLog(
            entity="Repair",
            entity_id=str(new_repair.id),
            action="CREATE",
            performed_by=user.id,
            diff=data.model_dump(),
        )
        session.add(audit)
        await session.commit()

        return RepairType(**new_repair.model_dump())


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=get_context)
