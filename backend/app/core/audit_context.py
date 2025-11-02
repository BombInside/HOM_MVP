from contextvars import ContextVar

# Текущий пользователь (устанавливается middleware)
current_user_id: ContextVar[int | None] = ContextVar("current_user_id", default=None)
