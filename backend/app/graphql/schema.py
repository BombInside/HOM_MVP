from typing import List
import strawberry
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_session
from ..models import Line, Machine


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
class Query:
    @strawberry.field
    async def lines(self, info) -> List[LineType]:
        session: AsyncSession = info.context["session"]
        result = await session.execute(select(Line).where(Line.is_deleted.is_(False)))
        return [
            LineType(id=l.id or 0, name=l.name, is_deleted=bool(l.is_deleted))
            for l in result.scalars().all()
        ]

    @strawberry.field
    async def machines(self, info) -> List[MachineType]:
        session: AsyncSession = info.context["session"]
        result = await session.execute(select(Machine).where(Machine.is_deleted.is_(False)))
        return [
            MachineType(
                id=m.id or 0,
                asset=m.asset,
                line_id=m.line_id,
                is_deleted=bool(m.is_deleted),
            )
            for m in result.scalars().all()
        ]


schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
