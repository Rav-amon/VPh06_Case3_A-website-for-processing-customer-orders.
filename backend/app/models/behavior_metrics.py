"""Живые метрики страницы: время, клики и позиции курсора для хитмапа."""

from __future__ import annotations

import asyncpg

from app.core.database import Database
from app.core.errors import AppError, map_postgres_error
from app.core.text import clean_text, require_int

MAX_TIME_ON_PAGE_SECONDS = 604_800
MAX_RETURN_FREQUENCY = 100_000
MAX_BUTTONS_CLICKED_LENGTH = 65_536
MAX_CURSOR_POSITIONS_LENGTH = 262_144
DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 100


def prepare_behavior_metrics(payload: dict[str, object]) -> dict[str, object]:
    """Проверяет пакет живых метрик перед записью."""
    application_id = require_int(
        payload.get('application_id', 0),
        label='application_id',
        minimum=0,
        maximum=2_147_483_647,
    )
    time_on_page = require_int(
        payload.get('time_on_page', 0),
        label='time_on_page',
        minimum=0,
        maximum=MAX_TIME_ON_PAGE_SECONDS,
    )
    return_frequency = require_int(
        payload.get('return_frequency', 0),
        label='return_frequency',
        minimum=0,
        maximum=MAX_RETURN_FREQUENCY,
    )
    buttons_clicked = clean_text(
        payload.get('buttons_clicked', ''),
        max_length=MAX_BUTTONS_CLICKED_LENGTH,
        label='buttons_clicked',
        required=False,
        single_line=False,
    )
    cursor_positions = clean_text(
        payload.get('cursor_positions', ''),
        max_length=MAX_CURSOR_POSITIONS_LENGTH,
        label='cursor_positions',
        required=False,
        single_line=False,
    )
    return {
        'application_id': application_id,
        'time_on_page': time_on_page,
        'buttons_clicked': buttons_clicked,
        'cursor_positions': cursor_positions,
        'return_frequency': return_frequency,
    }


class BehaviorMetrics:
    """Снимки поведения на главной странице для статистики и хитмапа.

    ```sql
    CREATE TABLE IF NOT EXISTS behavior_metrics (
        id BIGSERIAL PRIMARY KEY,
        application_id INTEGER NOT NULL DEFAULT 0,
        time_on_page INTEGER NOT NULL DEFAULT 0,
        buttons_clicked TEXT NOT NULL DEFAULT '',
        cursor_positions TEXT NOT NULL DEFAULT '',
        return_frequency INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT behavior_metrics_time_check CHECK (
            time_on_page >= 0
            AND time_on_page <= 604800
        ),
        CONSTRAINT behavior_metrics_return_check CHECK (
            return_frequency >= 0
            AND return_frequency <= 100000
        ),
        CONSTRAINT behavior_metrics_application_check CHECK (
            application_id >= 0
        ),
        CONSTRAINT behavior_metrics_length_check CHECK (
            char_length(buttons_clicked) <= 65536
            AND char_length(cursor_positions) <= 262144
        )
    );

    CREATE INDEX IF NOT EXISTS behavior_metrics_created_at_idx
        ON behavior_metrics (created_at DESC, id DESC);

    COMMENT ON TABLE behavior_metrics IS
        'Живые метрики главной: время, клики и позиции курсора.';
    COMMENT ON COLUMN behavior_metrics.time_on_page IS
        'Секунды, проведённые пользователем на странице.';
    COMMENT ON COLUMN behavior_metrics.buttons_clicked IS
        'JSON-строка счётчиков нажатий кнопок.';
    COMMENT ON COLUMN behavior_metrics.cursor_positions IS
        'JSON-строка точек курсора для хитмапа.';
    ```
    """

    table_name = 'behavior_metrics'
    columns = (
        'id',
        'application_id',
        'time_on_page',
        'buttons_clicked',
        'cursor_positions',
        'return_frequency',
        'created_at',
    )


class BehaviorMetricsCrud:
    """Создание и чтение живых метрик страницы."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def create(self, payload: dict[str, object]) -> dict[str, object]:
        """Сохраняет очередной снимок метрик."""
        data = prepare_behavior_metrics(payload)
        try:
            row = await self._database.fetchrow(
                '''
                INSERT INTO behavior_metrics (
                    application_id,
                    time_on_page,
                    buttons_clicked,
                    cursor_positions,
                    return_frequency
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                ''',
                data['application_id'],
                data['time_on_page'],
                data['buttons_clicked'],
                data['cursor_positions'],
                data['return_frequency'],
            )
        except asyncpg.PostgresError as error:
            raise map_postgres_error(error) from None
        if row is None:
            raise AppError(
                'database_error',
                'Метрики не сохранились',
                500,
                None,
            )
        return row

    async def get(self, metrics_id: int) -> dict[str, object]:
        """Возвращает один снимок метрик."""
        row = await self._database.fetchrow(
            'SELECT * FROM behavior_metrics WHERE id = $1',
            metrics_id,
        )
        if row is None:
            raise AppError('not_found', 'Метрики не найдены', 404, None)
        return row

    async def list_all(self, limit: int, offset: int) -> dict[str, object]:
        """Возвращает страницу снимков, новые сверху."""
        rows = await self._database.fetch(
            '''
            SELECT * FROM behavior_metrics
            ORDER BY created_at DESC, id DESC
            LIMIT $1 OFFSET $2
            ''',
            limit,
            offset,
        )
        total = await self._database.fetchval(
            'SELECT COUNT(*)::int FROM behavior_metrics'
        )
        return {
            'items': rows,
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    async def delete(self, metrics_id: int) -> dict[str, object]:
        """Удаляет снимок метрик."""
        row = await self._database.fetchrow(
            'DELETE FROM behavior_metrics WHERE id = $1 RETURNING id',
            metrics_id,
        )
        if row is None:
            raise AppError('not_found', 'Метрики не найдены', 404, None)
        return row
