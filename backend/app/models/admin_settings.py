"""Настройки интерфейса: услуги и диапазон бюджета для ползунка."""

from __future__ import annotations

import json
import re

import asyncpg

from app.core.database import Database
from app.core.errors import AppError, map_postgres_error
from app.core.text import clean_text, require_int

SINGLETON_ID = 1
MAX_SERVICES = 100
MAX_SERVICE_CODE_LENGTH = 64
MAX_SERVICE_TITLE_LENGTH = 200
MAX_SERVICE_DESCRIPTION_LENGTH = 2000
MAX_BUDGET_VALUE = 1_000_000_000
MAX_JSON_BYTES = 262_144
DEFAULT_BUDGET_MIN = 0
DEFAULT_BUDGET_MAX = 1_000_000
DEFAULT_BUDGET_STEP = 10_000

_SERVICE_CODE = re.compile(r'^[a-z0-9]+(?:[-_][a-z0-9]+)*$')


def default_settings() -> dict[str, object]:
    """Возвращает диапазон, который сайт показывает до первой правки."""
    return {
        'services': [],
        'budget_min': DEFAULT_BUDGET_MIN,
        'budget_max': DEFAULT_BUDGET_MAX,
        'budget_step': DEFAULT_BUDGET_STEP,
    }


def prepare_services(value: object) -> list[dict[str, object]]:
    """Проверяет список услуг, из которого сайт собирает форму."""
    if not isinstance(value, list):
        raise AppError(
            'invalid_data',
            '«услуги» должны быть списком',
            400,
            {'field': 'услуги'},
        )
    if len(value) > MAX_SERVICES:
        raise AppError(
            'invalid_data',
            f'Услуг больше {MAX_SERVICES}',
            400,
            {'field': 'услуги'},
        )
    prepared: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            raise AppError(
                'invalid_data',
                'Каждая услуга должна быть объектом',
                400,
                {'field': 'услуги'},
            )
        code = clean_text(
            item.get('code', ''),
            max_length=MAX_SERVICE_CODE_LENGTH,
            label='код услуги',
            required=True,
            single_line=True,
        ).lower()
        if _SERVICE_CODE.fullmatch(code) is None:
            raise AppError(
                'invalid_data',
                'Код услуги может содержать строчные латинские буквы, цифры, дефис и подчёркивание',
                400,
                {'field': 'код услуги'},
            )
        if code in seen:
            raise AppError(
                'invalid_data',
                'Коды услуг не должны повторяться',
                400,
                {'field': 'код услуги'},
            )
        seen.add(code)
        is_active = item.get('is_active', True)
        if not isinstance(is_active, bool):
            raise AppError(
                'invalid_data',
                '«услуга активна» должно быть да или нет',
                400,
                {'field': 'услуга активна'},
            )
        price_min = require_int(
            item.get('price_min'),
            label='минимум цены услуги',
            minimum=0,
            maximum=MAX_BUDGET_VALUE,
        )
        price_max = require_int(
            item.get('price_max'),
            label='максимум цены услуги',
            minimum=0,
            maximum=MAX_BUDGET_VALUE,
        )
        if price_max <= price_min:
            raise AppError(
                'invalid_data',
                'Максимум цены услуги должен быть больше минимума',
                400,
                {'field': 'максимум цены услуги', 'code': code},
            )
        prepared.append({
            'code': code,
            'title': clean_text(
                item.get('title', ''),
                max_length=MAX_SERVICE_TITLE_LENGTH,
                label='название услуги',
                required=True,
                single_line=True,
            ),
            'description': clean_text(
                item.get('description', ''),
                max_length=MAX_SERVICE_DESCRIPTION_LENGTH,
                label='описание услуги',
                required=False,
                single_line=False,
            ),
            'price_min': price_min,
            'price_max': price_max,
            'is_active': is_active,
        })
    encoded = json.dumps(prepared, ensure_ascii=False, separators=(',', ':'))
    if len(encoded.encode('utf-8')) > MAX_JSON_BYTES:
        raise AppError(
            'invalid_data',
            'Список услуг слишком большой',
            400,
            {'field': 'услуги'},
        )
    return prepared


def prepare_admin_settings(payload: dict[str, object]) -> dict[str, object]:
    """Проверяет услуги и диапазон ползунка."""
    budget_min = require_int(
        payload.get('budget_min'),
        label='минимум бюджета',
        minimum=0,
        maximum=MAX_BUDGET_VALUE,
    )
    budget_max = require_int(
        payload.get('budget_max'),
        label='максимум бюджета',
        minimum=0,
        maximum=MAX_BUDGET_VALUE,
    )
    budget_step = require_int(
        payload.get('budget_step'),
        label='шаг бюджета',
        minimum=1,
        maximum=MAX_BUDGET_VALUE,
    )
    if budget_max <= budget_min:
        raise AppError(
            'invalid_data',
            'Максимум бюджета должен быть больше минимума',
            400,
            {'field': 'максимум бюджета'},
        )
    services = prepare_services(payload.get('services', []))
    return {
        'services': json.dumps(services, ensure_ascii=False, separators=(',', ':')),
        'budget_min': budget_min,
        'budget_max': budget_max,
        'budget_step': budget_step,
    }


class AdminSettings:
    """Одна строка настроек, по которой сайт рисует форму.

    ```sql
    CREATE TABLE IF NOT EXISTS admin_settings (
        id SMALLINT PRIMARY KEY DEFAULT 1,
        services JSONB NOT NULL DEFAULT '[]'::jsonb,
        budget_min INTEGER NOT NULL,
        budget_max INTEGER NOT NULL,
        budget_step INTEGER NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT admin_settings_singleton CHECK (id = 1),
        CONSTRAINT admin_settings_budget_check CHECK (
            budget_min >= 0
            AND budget_max > budget_min
            AND budget_step > 0
            AND budget_max <= 1000000000
        ),
        CONSTRAINT admin_settings_services_array CHECK (
            jsonb_typeof(services) = 'array'
        ),
        CONSTRAINT admin_settings_services_size_check CHECK (
            octet_length(services::text) <= 262144
        )
    );

    COMMENT ON TABLE admin_settings IS
        'Услуги и диапазон бюджета. Фронтенд строит по этой строке форму.';
    COMMENT ON COLUMN admin_settings.services IS
        'Список услуг: code, title, description, price_min, price_max, is_active.';
    COMMENT ON COLUMN admin_settings.budget_min IS
        'Левый край ползунка бюджета.';
    COMMENT ON COLUMN admin_settings.budget_max IS
        'Правый край ползунка бюджета.';
    COMMENT ON COLUMN admin_settings.budget_step IS
        'Шаг ползунка бюджета.';
    ```
    """

    table_name = 'admin_settings'
    columns = (
        'id',
        'services',
        'budget_min',
        'budget_max',
        'budget_step',
        'updated_at',
    )


class AdminSettingsCrud:
    """Чтение и замена единственной строки настроек."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def ensure_defaults(self) -> None:
        """Создаёт строку настроек при первом запуске и не затирает правки."""
        defaults = default_settings()
        await self._database.execute(
            '''
            INSERT INTO admin_settings (
                id, services, budget_min, budget_max, budget_step
            )
            VALUES ($1, $2::jsonb, $3, $4, $5)
            ON CONFLICT (id) DO NOTHING
            ''',
            SINGLETON_ID,
            json.dumps(defaults['services'], ensure_ascii=False),
            defaults['budget_min'],
            defaults['budget_max'],
            defaults['budget_step'],
        )

    async def create(self, payload: dict[str, object]) -> dict[str, object]:
        """Создаёт единственную строку. Повторный вызов возвращает конфликт."""
        data = prepare_admin_settings(payload)
        try:
            row = await self._database.fetchrow(
                '''
                INSERT INTO admin_settings (
                    id, services, budget_min, budget_max, budget_step
                )
                VALUES ($1, $2::jsonb, $3, $4, $5)
                RETURNING *
                ''',
                SINGLETON_ID,
                data['services'],
                data['budget_min'],
                data['budget_max'],
                data['budget_step'],
            )
        except asyncpg.PostgresError as error:
            raise map_postgres_error(error) from None
        if row is None:
            raise AppError('database_error', 'Настройки не сохранились', 500, None)
        return row

    async def get(self) -> dict[str, object]:
        """Возвращает текущие настройки интерфейса."""
        row = await self._database.fetchrow(
            'SELECT * FROM admin_settings WHERE id = $1',
            SINGLETON_ID,
        )
        if row is None:
            raise AppError('not_found', 'Настройки не найдены', 404, None)
        return row

    async def list_all(self) -> dict[str, object]:
        """Возвращает ту же единственную строку списком из одного элемента."""
        rows = await self._database.fetch(
            'SELECT * FROM admin_settings ORDER BY id'
        )
        return {'items': rows, 'total': len(rows)}

    async def update(self, payload: dict[str, object]) -> dict[str, object]:
        """Заменяет услуги и диапазон бюджета целиком."""
        data = prepare_admin_settings(payload)
        try:
            row = await self._database.fetchrow(
                '''
                UPDATE admin_settings
                SET services = $2::jsonb,
                    budget_min = $3,
                    budget_max = $4,
                    budget_step = $5,
                    updated_at = NOW()
                WHERE id = $1
                RETURNING *
                ''',
                SINGLETON_ID,
                data['services'],
                data['budget_min'],
                data['budget_max'],
                data['budget_step'],
            )
        except asyncpg.PostgresError as error:
            raise map_postgres_error(error) from None
        if row is None:
            raise AppError('not_found', 'Настройки не найдены', 404, None)
        return row

    async def delete(self) -> dict[str, object]:
        """Возвращает диапазон по умолчанию. Строка остаётся, форма не пустеет."""
        defaults = prepare_admin_settings(default_settings())
        row = await self._database.fetchrow(
            '''
            UPDATE admin_settings
            SET services = $2::jsonb,
                budget_min = $3,
                budget_max = $4,
                budget_step = $5,
                updated_at = NOW()
            WHERE id = $1
            RETURNING *
            ''',
            SINGLETON_ID,
            defaults['services'],
            defaults['budget_min'],
            defaults['budget_max'],
            defaults['budget_step'],
        )
        if row is None:
            await self.ensure_defaults()
            return await self.get()
        return row
