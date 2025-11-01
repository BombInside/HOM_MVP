# -*- coding: utf-8 -*-
"""
Утилиты безопасности: хеширование паролей (bcrypt) и проверка.
"""
from __future__ import annotations
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Хэширует пароль пользователя, предварительно обрезая до 72 байт
    (ограничение алгоритма bcrypt).
    """
    # Обрезаем до 72 байт — чтобы не было ValueError при длинных/UTF-8 паролях
    safe_password = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(safe_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет пароль, применяя то же ограничение 72 байта.
    """
    safe_password = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.verify(safe_password, hashed_password)