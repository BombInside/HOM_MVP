from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None

class UserRoleLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    role_id: int = Field(foreign_key="role.id", primary_key=True)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    roles: List["Role"] = Relationship(back_populates="users", link_model=UserRoleLink)

Role.users = Relationship(back_populates="roles", link_model=UserRoleLink)

class Line(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    # EN: Soft delete flag for historical data integrity
    # RU: Флаг "мягкого" удаления для сохранения целостности исторических данных
    is_deleted: bool = Field(default=False)

class Machine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset: str = Field(index=True, unique=True)
    line_id: int = Field(foreign_key="line.id")
    # EN: Soft delete flag for historical data integrity
    # RU: Флаг "мягкого" удаления для сохранения целостности исторических данных
    is_deleted: bool = Field(default=False)

class Repair(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    machine_id: int = Field(foreign_key="machine.id")
    title: str
    description: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    created_by: int = Field(foreign_key="user.id")
    # EN: Soft delete flag for historical data integrity
    # RU: Флаг "мягкого" удаления для сохранения целостности исторических данных
    is_deleted: bool = Field(default=False)

class Downtime(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    machine_id: int = Field(foreign_key="machine.id")
    reason: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    created_by: int = Field(foreign_key="user.id")
    # EN: Soft delete flag for historical data integrity
    # RU: Флаг "мягкого" удаления для сохранения целостности исторических данных
    is_deleted: bool = Field(default=False)

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity: str
    entity_id: str
    action: str
    performed_by: Optional[int] = Field(default=None, foreign_key="user.id")
    at: datetime = Field(default_factory=datetime.utcnow)
    diff: Optional[dict] = Field(default=None, sa_column=Column(JSON))
