"""Настройки подключения. Пароль читается из окружения и в журнал не пишется."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

MAX_RETRY_COUNT = 3
RETRY_BASE_DELAY_SECONDS = 0.2
DEFAULT_POOL_MIN_SIZE = 1
DEFAULT_POOL_MAX_SIZE = 5
MAX_POOL_SIZE = 10
DEFAULT_POSTGRES_PORT = 5432

_ROLE_NAME = re.compile(r'^[A-Za-z0-9_]+$')
_PASSWORD = re.compile(r'^[A-Za-z0-9]+$')


@dataclass(frozen=True, repr=False)
class Settings:
    """Параметры пула. В текстовом представлении пароля нет."""

    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    pool_min_size: int
    pool_max_size: int

    def __repr__(self) -> str:
        return (
            f'Settings(host={self.postgres_host}, port={self.postgres_port}, '
            f'db={self.postgres_db}, user={self.postgres_user})'
        )


def _required(name: str) -> str:
    """Возвращает непустую переменную окружения."""
    value = os.environ.get(name, '').strip()
    if value == '':
        raise RuntimeError(f'Не задана переменная окружения {name}')
    return value


def _pool_size(name: str, default: int) -> int:
    """Читает размер пула и не даёт ему занять все соединения Postgres."""
    raw = os.environ.get(name, '').strip()
    if raw == '':
        return default
    if not raw.isdigit():
        raise RuntimeError(f'{name} должно быть целым числом')
    value = int(raw)
    if value < 1 or value > MAX_POOL_SIZE:
        raise RuntimeError(f'{name} должно быть от 1 до {MAX_POOL_SIZE}')
    return value


def load_settings() -> Settings:
    """Собирает настройки роли приложения, а не суперпользователя базы."""
    host = os.environ.get('POSTGRES_HOST', 'postgres').strip() or 'postgres'
    port_raw = os.environ.get('POSTGRES_PORT', str(DEFAULT_POSTGRES_PORT)).strip()
    if not port_raw.isdigit():
        raise RuntimeError('POSTGRES_PORT должно быть целым числом')
    port = int(port_raw)
    if port < 1 or port > 65535:
        raise RuntimeError('POSTGRES_PORT вне диапазона')

    user = _required('LEADS_APP_USER')
    password = _required('LEADS_APP_PASSWORD')
    database = _required('POSTGRES_DB')
    if _ROLE_NAME.fullmatch(user) is None:
        raise RuntimeError('LEADS_APP_USER содержит недопустимые символы')
    if _PASSWORD.fullmatch(password) is None:
        raise RuntimeError('LEADS_APP_PASSWORD содержит недопустимые символы')
    if _ROLE_NAME.fullmatch(database) is None:
        raise RuntimeError('POSTGRES_DB содержит недопустимые символы')

    pool_min_size = _pool_size('POSTGRES_POOL_MIN_SIZE', DEFAULT_POOL_MIN_SIZE)
    pool_max_size = _pool_size('POSTGRES_POOL_MAX_SIZE', DEFAULT_POOL_MAX_SIZE)
    if pool_min_size > pool_max_size:
        raise RuntimeError('Минимальный размер пула больше максимального')

    return Settings(
        postgres_host=host,
        postgres_port=port,
        postgres_db=database,
        postgres_user=user,
        postgres_password=password,
        pool_min_size=pool_min_size,
        pool_max_size=pool_max_size,
    )
