"""Хэширование паролей и выпуск JWT для панели администратора."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.errors import AppError

ALGORITHM = 'HS256'
TOKEN_TYPE = 'access'


def hash_password(password: str) -> str:
    """Возвращает bcrypt-хэш пароля."""
    digest = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return digest.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Сравнивает пароль с сохранённым хэшем без исключений наружу."""
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8'),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    *,
    subject: str,
    secret: str,
    expire_minutes: int,
    extra: dict[str, Any] | None = None,
) -> str:
    """Собирает JWT с сроком жизни и типом access."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        'sub': subject,
        'type': TOKEN_TYPE,
        'iat': now,
        'exp': now + timedelta(minutes=expire_minutes),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token: str, secret: str) -> dict[str, Any]:
    """Проверяет подпись и срок JWT. Чужие токены отклоняются."""
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as error:
        raise AppError(
            'unauthorized',
            'Срок действия токена истёк',
            401,
            None,
        ) from error
    except jwt.InvalidTokenError as error:
        raise AppError(
            'unauthorized',
            'Токен доступа недействителен',
            401,
            None,
        ) from error
    if payload.get('type') != TOKEN_TYPE:
        raise AppError(
            'unauthorized',
            'Токен доступа недействителен',
            401,
            None,
        )
    subject = payload.get('sub')
    if not isinstance(subject, str) or subject.strip() == '':
        raise AppError(
            'unauthorized',
            'Токен доступа недействителен',
            401,
            None,
        )
    return payload
