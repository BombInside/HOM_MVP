from typing import List, Optional
import strawberry
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..db import async_session
from ..models import Line, Machine


# ==========================
#  Strawberry GraphQL types
# ==========================

@strawberry.type
class MachineType:
    id: int
    name: str
    status: Optional[str]
    created_at: str


@strawberry.type
class LineType:
    id: int
    name: str
    description: Optional[str]
    created_at: str
    machines: List[MachineType]


# ==========================
#  Вспомогательные функции
# ==========================

async def get_db_session() -> AsyncSession:
    async with async_session() as session:
        yield session


# ==========================
#  Query (чтение данных)
# ==========================

@strawberry.type
class Query:
    @strawberry.field
    async def lines(self, info) -> List[LineType]:
        """Получить список всех линий с машинами."""
        async with async_session() as session:
            result = await session.execute(select(Line))
            lines = result.scalars().unique().all()
            # Загружаем связанные машины
            for line in lines:
                await session.refresh(line)
            return [
                LineType(
                    id=line.id,
                    name=line.name,
                    description=line.description,
                    created_at=line.created_at.isoformat(),
                    machines=[
                        MachineType(
                            id=m.id,
                            name=m.name,
                            status=m.status,
                            created_at=m.created_at.isoformat(),
                        )
                        for m in (line.machines or [])
                    ],
                )
                for line in lines
            ]

    @strawberry.field
    async def machines(self, info) -> List[MachineType]:
        """Получить список всех машин."""
        async with async_session() as session:
            result = await session.execute(select(Machine))
            machines = result.scalars().all()
            return [
                MachineType(
                    id=m.id,
                    name=m.name,
                    status=m.status,
                    created_at=m.created_at.isoformat(),
                )
                for m in machines
            ]


# ==========================
#  Mutation (изменение данных)
# ==========================

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_line(self, name: str, description: Optional[str] = None) -> LineType:
        """Создать новую производственную линию."""
        async with async_session() as session:
            new_line = Line(name=name, description=description)
            session.add(new_line)
            await session.commit()
            await session.refresh(new_line)
            return LineType(
                id=new_line.id,
                name=new_line.name,
                description=new_line.description,
                created_at=new_line.created_at.isoformat(),
                machines=[],
            )

    @strawberry.mutation
    async def create_machine(self, line_id: int, name: str, status: Optional[str] = None) -> MachineType:
        """Создать новую машину и привязать её к линии."""
        async with async_session() as session:
            new_machine = Machine(name=name, status=status, line_id=line_id)
            session.add(new_machine)
            await session.commit()
            await session.refresh(new_machine)
            return MachineType(
                id=new_machine.id,
                name=new_machine.name,
                status=new_machine.status,
                created_at=new_machine.created_at.isoformat(),
            )


# ==========================
#  Создание схемы
# ==========================

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
