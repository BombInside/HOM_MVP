# -*- coding: utf-8 -*-
import enum

class LineStatus(enum.Enum):
    working = "working"
    maintenance = "maintenance"
    stopped = "stopped"

class MachineStatus(enum.Enum):
    operational = "operational"
    broken = "broken"
    maintenance = "maintenance"

class RepairType(enum.Enum):
    scheduled = "scheduled"
    unscheduled = "unscheduled"

class RepairStatus(enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"
