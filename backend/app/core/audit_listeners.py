# -*- coding: utf-8 -*-
"""
События SQLAlchemy, записывающие изменения в таблицу audit_log.
"""

from datetime import datetime
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from app.core.audit_context import current_user_id
from app.models.audit_log import AuditLog


def _get_changed_fields(obj) -> tuple[dict, dict]:
    """Определяет старые и новые значения атрибутов модели."""
    state = inspect(obj)
    old_data, new_data = {}, {}
    for attr in state.attrs:
        if not attr.history.has_changes():
            continue
        old_val = attr.history.deleted[0] if attr.history.deleted else None
        new_val = attr.history.added[0] if attr.history.added else None
        # убираем служебные поля
        if attr.key in ("updated_at", "deleted_at", "created_at"):
            continue
        old_data[attr.key] = old_val
        new_data[attr.key] = new_val
    return old_data, new_data


def attach_audit_events(Base):
    """
    Подключает SQLAlchemy listeners для автоматического аудита изменений.
    """

    @event.listens_for(Session, "after_flush")
    def after_flush(session: Session, flush_context):
        uid = current_user_id.get()

        # CREATE
        for obj in session.new:
            if not hasattr(obj, "__tablename__"):
                continue
            table = obj.__tablename__
            new_data = {c: getattr(obj, c) for c in obj.__mapper__.columns.keys() if c != "updated_at"}
            entry = AuditLog(
                table_name=table,
                object_id=getattr(obj, "id", None),
                user_id=uid,
                action="CREATE",
                new_data=new_data,
                timestamp=datetime.utcnow(),
            )
            session.add(entry)

        # UPDATE
        for obj in session.dirty:
            if not hasattr(obj, "__tablename__") or not inspect(obj).attrs:
                continue
            table = obj.__tablename__
            old_data, new_data = _get_changed_fields(obj)
            if not old_data:
                continue
            entry = AuditLog(
                table_name=table,
                object_id=getattr(obj, "id", None),
                user_id=uid,
                action="UPDATE",
                old_data=old_data,
                new_data=new_data,
                timestamp=datetime.utcnow(),
            )
            session.add(entry)

        # DELETE
        for obj in session.deleted:
            if not hasattr(obj, "__tablename__"):
                continue
            table = obj.__tablename__
            old_data = {c: getattr(obj, c) for c in obj.__mapper__.columns.keys()}
            entry = AuditLog(
                table_name=table,
                object_id=getattr(obj, "id", None),
                user_id=uid,
                action="DELETE",
                old_data=old_data,
                timestamp=datetime.utcnow(),
            )
            session.add(entry)
