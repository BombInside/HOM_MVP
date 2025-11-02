from app.models.equipment import Machine
from app.schemas.machine import MachineCreate, MachineUpdate
from app.services.base import CRUDServiceBase

class MachineService(CRUDServiceBase[Machine, MachineCreate, MachineUpdate]):
    pass

machine_service = MachineService(Machine)
