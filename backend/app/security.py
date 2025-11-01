# -*- coding: utf-8 -*-
"""
Утилиты безопасности: хеширование паролей (bcrypt) и проверка.
"""
from __future__ import annotations
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Возвращает bcrypt-хеш пароля.
    :param plain_password: исходный пароль в открытом виде
    :return: str - безопасный хеш
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Проверяет соответствие пароля и хеша.
    :param plain_password: пароль
    :param password_hash: сохранённый хеш
    :return: bool
    """
    return pwd_context.verify(plain_password, password_hash)
