from fastapi import Request
from fastapi.responses import JSONResponse

async def json_error_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        # Add logging here (struct log / Sentry / OTEL)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "path": request.url.path},
        )
