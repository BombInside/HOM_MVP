from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_session
from ..models import Line, Machine
import strawberry

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
        res = await session.execute(select(Line).where(Line.is_deleted.is_(False)))
        return [LineType(id=l.id or 0, name=l.name, is_deleted=bool(l.is_deleted)) for l in res.scalars().all()]

    @strawberry.field
    async def machines(self, info) -> List[MachineType]:
        session: AsyncSession = info.context["session"]
        res = await session.execute(select(Machine).where(Machine.is_deleted.is_(False)))
        return [MachineType(id=m.id or 0, asset=m.asset, line_id=m.line_id, is_deleted=bool(m.is_deleted)) for m in res.scalars().all()]
