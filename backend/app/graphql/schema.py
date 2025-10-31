from __future__ import annotations

from typing import Any, Awaitable, Callable, List, Optional, TypeVar, cast

import strawberry
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from ..auth import get_current_user, has_role
from ..db import get_session
from ..models import AuditLog, Line, Machine, Repair, User  # noqa: F401

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def requires_role_graphql(required_role_name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        async def wrapper(*args: Any, info: Info, **kwargs: Any) -> Any:  # type: ignore
            user: User = info.context.get("user")
            if not user or not has_role(user, required_role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Requires role: {required_role_name}",
                )
            return await func(*args, info=info, **kwargs)

        return cast(F, wrapper)

    return decorator


async def get_context(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {"session": session, "user": current_user}


@strawberry.type
class LineType:
    id: int
    name: str
    is_deleted: bool


@strawberry.type
class MachineType:
    id: int
    name: str
    line_id: int
    is_deleted: bool


@strawberry.type
class RepairType:
    id: int
    machine_id: int
    description: Optional[str]
    created_by: int
    is_deleted: bool


@strawberry.input
class RepairCreateInput:
    machine_id: int
    description: Optional[str] = None


@strawberry.type
class Query:
    @strawberry.field
    async def lines(self, info: Info) -> List[LineType]:
        session: AsyncSession = info.context["session"]
        stmt = cast(Any, select(Line).where(Line.is_deleted == False))  # noqa: E712
        res = await session.execute(stmt)
        return [
            LineType(id=line.id or 0, name=line.name, is_deleted=bool(line.is_deleted))
            for line in res.scalars().all()
        ]

    @strawberry.field
    async def machines(self, info: Info) -> List[MachineType]:
        session: AsyncSession = info.context["session"]
        stmt = cast(Any, select(Machine).where(Machine.is_deleted == False))  # noqa: E712
        res = await session.execute(stmt)
        return [
            MachineType(
                id=machine.id or 0,
                name=machine.name,
                line_id=machine.line_id,
                is_deleted=bool(machine.is_deleted),
            )
            for machine in res.scalars().all()
        ]


@strawberry.type
class Mutation:
    @strawberry.mutation
    @requires_role_graphql("Admin")
    async def create_line(self, info: Info, name: str) -> LineType:
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

        return LineType(id=new_line.id or 0, name=new_line.name, is_deleted=False)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app: GraphQLRouter = GraphQLRouter(schema, context_getter=get_context)
