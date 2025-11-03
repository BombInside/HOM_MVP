from app.models.equipment import Line
from app.schemas.line import LineCreate, LineUpdate
from app.services.base import CRUDServiceBase

class LineService(CRUDServiceBase[Line, LineCreate, LineUpdate]):
    pass

line_service = LineService(Line)
