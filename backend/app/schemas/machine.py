from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MachineBase(BaseModel):
    line_id: int
    name: str
    asset_number: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = "operational"
    last_repair_date: Optional[date] = None
    hours_since_last_repair: Optional[int] = 0
    notes: Optional[str] = None
    is_active: Optional[bool] = True


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MachineOut(MachineBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
