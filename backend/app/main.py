# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from app.config import get_settings
from app.db import wait_for_db_ready

# api routers
from app.routes_auth import router as auth_router
from app.admin_panel import router as admin_router
from app.api.adminpanel import roles as roles_router
from app.api.adminpanel import permissions as permissions_router
from app.api.system import router as system_router

from app.api.equipment import lines, machines, repairs, repair_attachments
from app.api import audit_log

from app.middleware.audit_middleware import AuditUserMiddleware


logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0",
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET or "unsafe")
app.add_middleware(AuditUserMiddleware)

# ======== STATIC FILES (FRONTEND) ========
DIST_PATH = "/app/frontend/dist"
if os.path.exists(DIST_PATH):
    print("📦 Serving frontend from:", DIST_PATH)
    app.mount("/", StaticFiles(directory=DIST_PATH, html=True), name="frontend")
else:
    print("⚠️ No frontend dist directory found:", DIST_PATH)

# ======== API ROUTES ========
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(system_router)

app.include_router(roles_router.router, prefix="/adminpanel")
app.include_router(permissions_router.router, prefix="/adminpanel")

app.include_router(lines.router, prefix="/api")
app.include_router(machines.router, prefix="/api")
app.include_router(repairs.router, prefix="/api")
app.include_router(repair_attachments.router, prefix="/api")
app.include_router(audit_log.router, prefix="/api")

# ======== SPA FALLBACK ========
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """
    Перехватывает ВСЕ неизвестные пути
    и возвращает index.html для SPA.
    """
    index_file = os.path.join(DIST_PATH, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"error": "index.html not found"}


# Startup
@app.on_event("startup")
async def on_startup():
    await wait_for_db_ready()
    logger.info("🚀 Backend ready")
