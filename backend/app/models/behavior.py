"""Метрики поведения на странице. Связь с заявкой один к одному."""

from __future__ import annotations

import json

import asyncpg

from app.core.database import Database
from app.core.errors import AppError, map_postgres_error
from app.core.text import assert_identifier, clean_text, require_int

MAX_TIME_ON_PAGE_MS = 604_800_000
MAX_RETURN_COUNT = 100_000
MAX_BEHAVIOR_EVENTS = 200
MAX_BUTTON_NAME_LENGTH = 100
MAX_SELECTOR_LENGTH = 200
MAX_CURSOR_POSITION = 100_000
MAX_EVENT_DURATION_MS = 3_600_000
MAX_USER_AGENT_LENGTH = 512
MAX_LANGUAGE_LENGTH = 32
MAX_TIMEZONE_LENGTH = 64
MAX_SCREEN_LENGTH = 32
MAX_REFERRER_LENGTH = 1000
MAX_JSON_BYTES = 262_144

_BEHAVIOR_FIELDS = (
    'lead_id',
    'time_on_page_ms',
    'button_clicks',
    'cursor_hotspots',
    'return_count',
    'user_agent',
    'language',
    'timezone',
    'screen',
    'referrer',
)


def _events(value: object, label: str) -> list[object]:
    """Проверяет, что метрика пришла списком ограниченной длины."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise AppError(
            'invalid_data',
            f'«{label}» должно быть списком',
            400,
            {'field': label},
        )
    if len(value) > MAX_BEHAVIOR_EVENTS:
        raise AppError(
            'invalid_data',
            f'«{label}» содержит больше {MAX_BEHAVIOR_EVENTS} элементов',
            400,
            {'field': label},
        )
    return value


def prepare_button_clicks(value: object) -> list[dict[str, object]]:
    """Оставляет имя кнопки и число нажатий."""
    prepared: list[dict[str, object]] = []
    for item in _events(value, 'нажатия кнопок'):
        if not isinstance(item, dict):
            raise AppError(
                'invalid_data',
                'Каждое нажатие должно быть объектом с именем и числом',
                400,
                {'field': 'нажатия кнопок'},
            )
        name = clean_text(
            item.get('name', ''),
            max_length=MAX_BUTTON_NAME_LENGTH,
            label='кнопка',
            required=True,
            single_line=True,
        )
        count = require_int(
            item.get('count'),
            label='число нажатий',
            minimum=0,
            maximum=MAX_RETURN_COUNT,
        )
        prepared.append({'name': name, 'count': count})
    return prepared


def prepare_cursor_hotspots(value: object) -> list[dict[str, object]]:
    """Оставляет точку, длительность зависания и селектор."""
    prepared: list[dict[str, object]] = []
    for item in _events(value, 'зависания курсора'):
        if not isinstance(item, dict):
            raise AppError(
                'invalid_data',
                'Каждое зависание курсора должно быть объектом',
                400,
                {'field': 'зависания курсора'},
            )
        selector = clean_text(
            item.get('selector', ''),
            max_length=MAX_SELECTOR_LENGTH,
            label='селектор',
            required=False,
            single_line=True,
        )
        prepared.append({
            'x': require_int(
                item.get('x'),
                label='координата x',
                minimum=0,
                maximum=MAX_CURSOR_POSITION,
            ),
            'y': require_int(
                item.get('y'),
                label='координата y',
                minimum=0,
                maximum=MAX_CURSOR_POSITION,
            ),
            'duration_ms': require_int(
                item.get('duration_ms'),
                label='длительность зависания',
                minimum=0,
                maximum=MAX_EVENT_DURATION_MS,
            ),
            'selector': selector,
        })
    return prepared


def prepare_behavior(payload: dict[str, object]) -> dict[str, object]:
    """Проверяет пакет метрик перед записью."""
    clicks = prepare_button_clicks(payload.get('button_clicks', []))
    hotspots = prepare_cursor_hotspots(payload.get('cursor_hotspots', []))
    clicks_json = json.dumps(clicks, ensure_ascii=False, separators=(',', ':'))
    hotspots_json = json.dumps(hotspots, ensure_ascii=False, separators=(',', ':'))
    if len(clicks_json.encode('utf-8')) > MAX_JSON_BYTES:
        raise AppError(
            'invalid_data',
            'Пакет нажатий слишком большой',
            400,
            {'field': 'нажатия кнопок'},
        )
    if len(hotspots_json.encode('utf-8')) > MAX_JSON_BYTES:
        raise AppError(
            'invalid_data',
            'Пакет зависаний курсора слишком большой',
            400,
            {'field': 'зависания курсора'},
        )
    return {
        'lead_id': require_int(
            payload.get('lead_id'),
            label='идентификатор заявки',
            minimum=1,
            maximum=9_223_372_036_854_775_807,
        ),
        'time_on_page_ms': require_int(
            payload.get('time_on_page_ms'),
            label='время на странице',
            minimum=0,
            maximum=MAX_TIME_ON_PAGE_MS,
        ),
        'button_clicks': clicks_json,
        'cursor_hotspots': hotspots_json,
        'return_count': require_int(
            payload.get('return_count'),
            label='число возвратов',
            minimum=0,
            maximum=MAX_RETURN_COUNT,
        ),
        'user_agent': clean_text(
            payload.get('user_agent', ''),
            max_length=MAX_USER_AGENT_LENGTH,
            label='браузер',
            required=False,
            single_line=True,
        ),
        'language': clean_text(
            payload.get('language', ''),
            max_length=MAX_LANGUAGE_LENGTH,
            label='язык',
            required=False,
            single_line=True,
        ),
        'timezone': clean_text(
            payload.get('timezone', ''),
            max_length=MAX_TIMEZONE_LENGTH,
            label='часовой пояс',
            required=False,
            single_line=True,
        ),
        'screen': clean_text(
            payload.get('screen', ''),
            max_length=MAX_SCREEN_LENGTH,
            label='экран',
            required=False,
            single_line=True,
        ),
        'referrer': clean_text(
            payload.get('referrer', ''),
            max_length=MAX_REFERRER_LENGTH,
            label='источник перехода',
            required=False,
            single_line=True,
        ),
    }


def _insert_sql() -> str:
    """Собирает INSERT метрик из постоянного списка колонок."""
    columns = ', '.join(assert_identifier(name) for name in _BEHAVIOR_FIELDS)
    numbers = ', '.join(
        f'${index}' for index in range(1, len(_BEHAVIOR_FIELDS) + 1)
    )
    return (
        f'INSERT INTO lead_behavior ({columns}) VALUES ({numbers}) RETURNING *'
    )


def _update_sql() -> str:
    """Обновляет метрики той же заявки. Ключ не меняется."""
    mutable = [name for name in _BEHAVIOR_FIELDS if name != 'lead_id']
    assignments = ', '.join(
        f'{assert_identifier(column)} = ${index}'
        for index, column in enumerate(mutable, start=2)
    )
    return (
        f'UPDATE lead_behavior SET {assignments}, updated_at = NOW() '
        f'WHERE lead_id = $1 RETURNING *'
    )


def _behavior_values(data: dict[str, object]) -> tuple[object, ...]:
    """Возвращает значения в порядке колонок INSERT."""
    return tuple(data[field] for field in _BEHAVIOR_FIELDS)


class LeadBehavior:
    """Поведение посетителя. Первичный ключ совпадает с id заявки.

    Отдельного суррогатного ключа нет: одна заявка — одна строка метрик.

    ```sql
    CREATE TABLE IF NOT EXISTS lead_behavior (
        lead_id BIGINT PRIMARY KEY REFERENCES leads (id) ON DELETE CASCADE,
        time_on_page_ms INTEGER NOT NULL,
        button_clicks JSONB NOT NULL DEFAULT '[]'::jsonb,
        cursor_hotspots JSONB NOT NULL DEFAULT '[]'::jsonb,
        return_count INTEGER NOT NULL,
        user_agent TEXT NOT NULL DEFAULT '',
        language VARCHAR(32) NOT NULL DEFAULT '',
        timezone VARCHAR(64) NOT NULL DEFAULT '',
        screen VARCHAR(32) NOT NULL DEFAULT '',
        referrer TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT lead_behavior_ranges_check CHECK (
            time_on_page_ms >= 0
            AND time_on_page_ms <= 604800000
            AND return_count >= 0
            AND return_count <= 100000
        ),
        CONSTRAINT lead_behavior_clicks_array CHECK (
            jsonb_typeof(button_clicks) = 'array'
        ),
        CONSTRAINT lead_behavior_hotspots_array CHECK (
            jsonb_typeof(cursor_hotspots) = 'array'
        ),
        CONSTRAINT lead_behavior_length_check CHECK (
            char_length(user_agent) <= 512
            AND char_length(language) <= 32
            AND char_length(timezone) <= 64
            AND char_length(screen) <= 32
            AND char_length(referrer) <= 1000
            AND octet_length(button_clicks::text) <= 262144
            AND octet_length(cursor_hotspots::text) <= 262144
        )
    );

    COMMENT ON TABLE lead_behavior IS
        'Метрики страницы. Первичный ключ равен leads.id, связь один к одному.';
    COMMENT ON COLUMN lead_behavior.lead_id IS
        'Тот же идентификатор, что у заявки. Вторая строка на заявку невозможна.';
    COMMENT ON COLUMN lead_behavior.time_on_page_ms IS
        'Сколько миллисекунд человек провёл на странице.';
    COMMENT ON COLUMN lead_behavior.return_count IS
        'Сколько раз человек возвращался на страницу.';
    ```
    """

    table_name = 'lead_behavior'
    columns = (
        *_BEHAVIOR_FIELDS,
        'created_at',
        'updated_at',
    )


class LeadBehaviorCrud:
    """Запись и чтение метрик. Ключ строки — идентификатор заявки."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def create(self, payload: dict[str, object]) -> dict[str, object]:
        """Сохраняет первый пакет метрик для заявки."""
        data = prepare_behavior(payload)
        try:
            row = await self._database.fetchrow(
                _insert_sql(),
                *_behavior_values(data),
            )
        except asyncpg.PostgresError as error:
            raise map_postgres_error(error) from None
        if row is None:
            raise AppError('database_error', 'Метрики не сохранились', 500, None)
        return row

    async def get(self, lead_id: int) -> dict[str, object]:
        """Возвращает метрики одной заявки."""
        row = await self._database.fetchrow(
            'SELECT * FROM lead_behavior WHERE lead_id = $1',
            lead_id,
        )
        if row is None:
            raise AppError('not_found', 'Метрики не найдены', 404, None)
        return row

    async def list_all(self, limit: int, offset: int) -> dict[str, object]:
        """Возвращает страницу метрик."""
        rows = await self._database.fetch(
            '''
            SELECT * FROM lead_behavior
            ORDER BY created_at DESC, lead_id DESC
            LIMIT $1 OFFSET $2
            ''',
            limit,
            offset,
        )
        total = await self._database.fetchval(
            'SELECT COUNT(*)::int FROM lead_behavior'
        )
        return {
            'items': rows,
            'total': total,
            'limit': limit,
            'offset': offset,
        }

    async def update(
        self,
        lead_id: int,
        payload: dict[str, object],
    ) -> dict[str, object]:
        """Заменяет метрики уже существующей заявки."""
        merged = dict(payload)
        merged['lead_id'] = lead_id
        data = prepare_behavior(merged)
        mutable = [name for name in _BEHAVIOR_FIELDS if name != 'lead_id']
        try:
            row = await self._database.fetchrow(
                _update_sql(),
                lead_id,
                *(data[name] for name in mutable),
            )
        except asyncpg.PostgresError as error:
            raise map_postgres_error(error) from None
        if row is None:
            raise AppError('not_found', 'Метрики не найдены', 404, None)
        return row

    async def delete(self, lead_id: int) -> dict[str, object]:
        """Удаляет метрики и оставляет саму заявку."""
        row = await self._database.fetchrow(
            'DELETE FROM lead_behavior WHERE lead_id = $1 RETURNING lead_id',
            lead_id,
        )
        if row is None:
            raise AppError('not_found', 'Метрики не найдены', 404, None)
        return row
