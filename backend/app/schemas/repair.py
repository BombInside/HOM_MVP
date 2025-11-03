from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RepairBase(BaseModel):
    machine_id: int
    asset_number: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    actions_taken: Optional[str] = None
    performed_by: Optional[int] = None
    created_by: int
    updated_by: Optional[int] = None
    repair_type: Optional[str] = "unscheduled"
    status: Optional[str] = "open"
    cost: Optional[float] = None
    parts_used: Optional[str] = None
    downtime_hours: Optional[float] = None


class RepairCreate(RepairBase):
    pass


class RepairUpdate(BaseModel):
    description: Optional[str] = None
    actions_taken: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[datetime] = None
    updated_by: Optional[int] = None
    downtime_hours: Optional[float] = None


class RepairOut(RepairBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
