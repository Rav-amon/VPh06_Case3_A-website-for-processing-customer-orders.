"""Проверка, что процесс и база отвечают."""

import asyncpg
from fastapi import APIRouter, Depends

from app.core.database import Database
from app.core.errors import AppError
from app.core.responses import success
from app.routes.deps import get_database

router = APIRouter(tags=['служба'])


@router.get('/health')
async def read_health(
    database: Database = Depends(get_database),
) -> dict[str, object]:
    """Проверяет соединение с PostgreSQL."""
    try:
        await database.fetchval('SELECT 1')
    except (OSError, TimeoutError, asyncpg.PostgresError) as error:
        raise AppError(
            'database_unavailable',
            'База недоступна',
            503,
            None,
        ) from error
    return success({'status': 'ok'}, 'Сервис доступен')
