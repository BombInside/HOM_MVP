from __future__ import annotations

from typing import Any, Awaitable, Callable, List, Optional, TypeVar, cast

import strawberry
from sqlalchemy import not_, select
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from fastapi import Depends, status, HTTPException

from ..auth import get_current_user, has_role
from ..db import get_session
from ..models import AuditLog, Line, Machine, Repair, User

# =========================
# Контекст
# =========================


async def get_context(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {"session": session, "user": current_user}


# =========================
# RBAC декоратор (типобезопасный)
# =========================

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def requires_role_graphql(required_role_name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        async def wrapper(*args: Any, info: Info, **kwargs: Any) -> Any:  # type: ignore[override]
            user: User = info.context.get("user")
            if not user or not has_role(user, required_role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Requires role: {required_role_name}",
                )
            return await func(*args, info=info, **kwargs)

        return cast(F, wrapper)

    return decorator


# =========================
# GraphQL типы
# =========================


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
    description: Optional[str]
    started_at: strawberry.scalar(str)  # упрощённый scalar для региональной совместимости
    finished_at: Optional[strawberry.scalar(str)]
    created_by: int
    is_deleted: bool


@strawberry.input
class RepairCreateInput:
    machine_id: int
    title: str
    description: Optional[str] = None
    started_at: strawberry.scalar(str)
    finished_at: Optional[strawberry.scalar(str)] = None


# =========================
# Query
# =========================


@strawberry.type
class Query:
    @strawberry.field
    async def lines(self, info: Info) -> List[LineType]:
        session: AsyncSession = info.context["session"]
        res = await session.execute(select(Line).where(not_(Line.is_deleted)))
        items = res.scalars().all()
        out: List[LineType] = []
        for line in items:
            assert line.id is not None  # для mypy: в БД записанные строки всегда с id
            out.append(
                LineType(
                    id=line.id,
                    name=line.name,
                    is_deleted=bool(line.is_deleted),
                )
            )
        return out

    @strawberry.field
    async def machines(self, info: Info) -> List[MachineType]:
        session: AsyncSession = info.context["session"]
        res = await session.execute(select(Machine).where(not_(Machine.is_deleted)))
        items = res.scalars().all()
        out: List[MachineType] = []
        for machine in items:
            assert machine.id is not None
            out.append(
                MachineType(
                    id=machine.id,
                    asset=machine.asset,  # убедитесь, что в модели поле называется `asset`
                    line_id=machine.line_id,
                    is_deleted=bool(machine.is_deleted),
                )
            )
        return out


# =========================
# Mutations
# =========================


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

        # audit
        audit = AuditLog(
            entity="Line",
            entity_id=str(new_line.id),
            action="CREATE",
            performed_by=user.id,
            diff={"name": name},
        )
        session.add(audit)
        await session.commit()

        assert new_line.id is not None
        return LineType(id=new_line.id, name=new_line.name, is_deleted=bool(new_line.is_deleted))

    @strawberry.mutation
    @requires_role_graphql("Technician")
    async def create_repair(self, info: Info, data: RepairCreateInput) -> RepairType:
        session: AsyncSession = info.context["session"]
        user: User = info.context["user"]

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
                "started_at": data.started_at,
                "finished_at": data.finished_at,
            },
        )
        session.add(audit)
        await session.commit()

        assert new_repair.id is not None
        return RepairType(
            id=new_repair.id,
            machine_id=new_repair.machine_id,
            title=new_repair.title,
            description=new_repair.description,
            started_at=str(new_repair.started_at),
            finished_at=str(new_repair.finished_at) if new_repair.finished_at else None,
            created_by=new_repair.created_by,
            is_deleted=bool(new_repair.is_deleted),
        )


# =========================
# Schema & Router
# =========================

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app: GraphQLRouter = GraphQLRouter(schema, context_getter=get_context)
