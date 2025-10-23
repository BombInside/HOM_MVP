import strawberry
from typing import List
from fastapi import Depends
from strawberry.fastapi import GraphQLRouter
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import async_session
from ..models import Line, Machine

async def get_session() -> AsyncSession:
    async with async_session() as s:
        yield s

@strawberry.type
class LineType:
    id: int
    name: str

@strawberry.type
class MachineType:
    id: int
    asset: str
    line_id: int

@strawberry.type
class Query:
    @strawberry.field
    async def lines(self, info) -> List[LineType]:
        session: AsyncSession = info.context["session"]
        res = await session.execute(select(Line))
        return [LineType(id=l.id, name=l.name) for l in res.scalars().all()]

    @strawberry.field
    async def machines(self, info) -> List[MachineType]:
        session: AsyncSession = info.context["session"]
        res = await session.execute(select(Machine))
        return [MachineType(id=m.id, asset=m.asset, line_id=m.line_id) for m in res.scalars().all()]

schema = strawberry.Schema(query=Query)

def get_context(session: AsyncSession = Depends(get_session)):
    return {"session": session}

graphql_app = GraphQLRouter(schema, context_getter=get_context)
