from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column, JSON


class UserRoleLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.id", primary_key=True)


class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None

    users: List["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    roles: List[Role] = Relationship(back_populates="users", link_model=UserRoleLink)


class Line(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    is_deleted: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Machine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    line_id: int = Field(foreign_key="line.id", index=True)
    name: str = Field(index=True)
    is_deleted: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    line: Optional[Line] = Relationship()


class Repair(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    machine_id: int = Field(foreign_key="machine.id", index=True)
    description: str
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    finished_at: Optional[datetime] = None
    created_by: int = Field(foreign_key="user.id", index=True)
    is_deleted: bool = Field(default=False, index=True)

    machine: Optional[Machine] = Relationship()
    creator: Optional[User] = Relationship()


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity: str
    entity_id: str
    action: str
    performed_by: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    at: datetime = Field(default_factory=datetime.utcnow, index=True)
    diff: Optional[dict] = Field(default=None, sa_column=Column(JSON))
