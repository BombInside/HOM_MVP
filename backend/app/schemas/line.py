from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LineBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    status: Optional[str] = "working"
    is_active: Optional[bool] = True
    notes: Optional[str] = None


class LineCreate(LineBase):
    pass


class LineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class LineOut(LineBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
