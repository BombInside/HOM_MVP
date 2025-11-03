from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.audit_context import current_user_id

class AuditUserMiddleware(BaseHTTPMiddleware):
    """
    Middleware для записи user_id в contextvars.
    Используется для автоматического логирования действий.
    """
    async def dispatch(self, request: Request, call_next):
        user = getattr(request.state, "user", None)
        user_id = getattr(user, "id", None) if user else None
        current_user_id.set(user_id)
        response = await call_next(request)
        return response
