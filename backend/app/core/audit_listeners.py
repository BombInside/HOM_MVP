from __future__ import annotations
from datetime import datetime
from typing import Any
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.core.audit_context import current_user_id

LINK_TABLES = {"user_role_link", "role_permission_link"}

def _jsonify(v: Any):
    if isinstance(v, datetime):
        return v.isoformat()
    return v
    

def _snapshot(obj) -> dict:
    return {c.key: _jsonify(getattr(obj, c.key)) for c in obj.__table__.columns}

@event.listens_for(Session, "before_flush")
def before_flush(session: Session, *_):
    uid = current_user_id.get()

    for obj in session.new:
        if not hasattr(obj, "__tablename__"):
            continue
        table = obj.__tablename__
        data = _snapshot(obj)

        if table in LINK_TABLES:
            object_id = None
        else:
            object_id = getattr(obj, "id", None)

        session.add(AuditLog(
            table_name=table,
            object_id=object_id,
            user_id=uid,
            action="CREATE",
            old_data=None,
            new_data=data,
            timestamp=datetime.utcnow(),
        ))

    for obj in session.dirty:
        if not hasattr(obj, "__tablename__"):
            continue
        table = obj.__tablename__
        if table in LINK_TABLES:
            continue

        state = inspect(obj)
        changes = {
            k: {"old": _jsonify(v.deleted[0]) if v.deleted else None, "new": _jsonify(v.value)}
            for k, v in state.attrs.items() if v.history.has_changes()
        }

        if changes:
            session.add(AuditLog(
                table_name=table,
                object_id=getattr(obj, "id", None),
                user_id=uid,
                action="UPDATE",
                old_data={k: v["old"] for k, v in changes.items()},
                new_data={k: v["new"] for k, v in changes.items()},
                timestamp=datetime.utcnow(),
            ))

    for obj in session.deleted:
        if not hasattr(obj, "__tablename__"):
            continue
        table = obj.__tablename__
        data = _snapshot(obj)
        session.add(AuditLog(
            table_name=table,
            object_id=getattr(obj, "id", None),
            user_id=uid,
            action="DELETE",
            old_data=data,
            new_data=None,
            timestamp=datetime.utcnow(),
        ))
