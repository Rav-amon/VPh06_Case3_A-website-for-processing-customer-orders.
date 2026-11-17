"""Пул соединений с PostgreSQL. Снаружи базы к ней хода нет."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import TypeVar

import asyncpg

from app.core.config import (
    MAX_RETRY_COUNT,
    RETRY_BASE_DELAY_SECONDS,
    Settings,
)
from app.core.logging import log_event

T = TypeVar('T')

JSON_FIELDS = frozenset({'button_clicks', 'cursor_hotspots', 'services'})

TRANSIENT_ERRORS = (
    asyncpg.CannotConnectNowError,
    asyncpg.ConnectionDoesNotExistError,
    asyncpg.InterfaceError,
    asyncpg.TooManyConnectionsError,
    asyncpg.PostgresConnectionError,
    OSError,
    TimeoutError,
)


def row_to_dict(row: asyncpg.Record) -> dict[str, object]:
    """Превращает строку базы в словарь, пригодный для JSON."""
    result: dict[str, object] = {}
    for key, value in row.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
            continue
        if key in JSON_FIELDS and isinstance(value, str):
            result[key] = json.loads(value)
            continue
        result[key] = value
    return result


class Database:
    """Драйвер: повтор кратких обрывов и запросы только с параметрами."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def connect(cls, settings: Settings) -> Database:
        """Открывает пул от имени роли приложения."""
        delay = RETRY_BASE_DELAY_SECONDS
        for attempt in range(1, MAX_RETRY_COUNT + 1):
            try:
                pool = await asyncpg.create_pool(
                    host=settings.postgres_host,
                    port=settings.postgres_port,
                    database=settings.postgres_db,
                    user=settings.postgres_user,
                    password=settings.postgres_password,
                    min_size=settings.pool_min_size,
                    max_size=settings.pool_max_size,
                    command_timeout=10,
                    server_settings={
                        'application_name': 'leads_backend',
                        'timezone': 'UTC',
                    },
                )
                if pool is None:
                    raise RuntimeError('Пул соединений не создан')
                return cls(pool)
            except TRANSIENT_ERRORS as error:
                log_event(
                    logging.WARNING,
                    'не удалось открыть пул базы',
                    {
                        'attempt': attempt,
                        'error_type': type(error).__name__,
                    },
                )
                if attempt == MAX_RETRY_COUNT:
                    raise RuntimeError(
                        'Не удалось подключиться к PostgreSQL'
                    ) from None
                await asyncio.sleep(delay)
                delay *= 2
        raise RuntimeError('Не удалось подключиться к PostgreSQL')

    async def close(self) -> None:
        """Закрывает пул при остановке процесса."""
        await self._pool.close()

    async def fetch(
        self,
        query: str,
        *args: object,
    ) -> list[dict[str, object]]:
        """Возвращает все строки запроса."""

        async def operation() -> list[dict[str, object]]:
            async with self._pool.acquire() as connection:
                rows = await connection.fetch(query, *args)
            return [row_to_dict(row) for row in rows]

        return await self._retry(operation)

    async def fetchrow(
        self,
        query: str,
        *args: object,
    ) -> dict[str, object] | None:
        """Возвращает одну строку или None."""

        async def operation() -> dict[str, object] | None:
            async with self._pool.acquire() as connection:
                row = await connection.fetchrow(query, *args)
            if row is None:
                return None
            return row_to_dict(row)

        return await self._retry(operation)

    async def fetchval(self, query: str, *args: object) -> object:
        """Возвращает первое значение первой строки."""

        async def operation() -> object:
            async with self._pool.acquire() as connection:
                return await connection.fetchval(query, *args)

        return await self._retry(operation)

    async def execute(self, query: str, *args: object) -> None:
        """Выполняет команду без возврата строк клиенту."""

        async def operation() -> None:
            async with self._pool.acquire() as connection:
                await connection.execute(query, *args)

        await self._retry(operation)

    async def _retry(self, operation: Callable[[], Awaitable[T]]) -> T:
        """Повторяет обрыв соединения. Ошибки данных не повторяет."""
        delay = RETRY_BASE_DELAY_SECONDS
        for attempt in range(1, MAX_RETRY_COUNT + 1):
            try:
                return await operation()
            except TRANSIENT_ERRORS as error:
                log_event(
                    logging.WARNING,
                    'повтор запроса к базе',
                    {
                        'attempt': attempt,
                        'error_type': type(error).__name__,
                    },
                )
                if attempt == MAX_RETRY_COUNT:
                    raise
                await asyncio.sleep(delay)
                delay *= 2
        raise RuntimeError('Повтор запроса завершился без результата')
