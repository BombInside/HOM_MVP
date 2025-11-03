# -*- coding: utf-8 -*-
"""
Утилиты безопасности: хеширование паролей (bcrypt) и проверка.
"""
from __future__ import annotations
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_for_bcrypt(s: str) -> str:
    """bcrypt учитывает максимум ~72 байта. Чтобы избежать ValueError из бэкенда,
    безопасно обрежем ввод по байтам UTF‑8.
    """
    b = s.encode("utf-8")
    if len(b) > 72:
        b = b[:72]
        try:
            return b.decode("utf-8")
        except UnicodeDecodeError:
            # обрежем до ближайшей валидной границы
            return b.decode("utf-8", errors="ignore")
    return s


def hash_password(plain_password: str) -> str:
    """Возвращает bcrypt-хеш пароля."""
    return pwd_context.hash(_truncate_for_bcrypt(plain_password))


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Проверяет соответствие пароля и хеша."""
    return pwd_context.verify(_truncate_for_bcrypt(plain_password), password_hash)
