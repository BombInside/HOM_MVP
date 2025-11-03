# -*- coding: utf-8 -*-
"""
Pydantic-схемы для AuditLog API
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    id: int
    table_name: str
    object_id: int
    user_id: Optional[int] = None
    action: str
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
