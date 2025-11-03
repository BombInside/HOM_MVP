from app.models.equipment import Repair
from app.schemas.repair import RepairCreate, RepairUpdate
from app.services.base import CRUDServiceBase

class RepairService(CRUDServiceBase[Repair, RepairCreate, RepairUpdate]):
    pass

repair_service = RepairService(Repair)
