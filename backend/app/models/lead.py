"""Заявка тёплого клиента и операции с её строкой."""

from __future__ import annotations

import asyncpg

from app.core.database import Database
from app.core.errors import AppError, map_postgres_error
from app.core.text import (
    assert_identifier,
    clean_email,
    clean_phone,
    clean_text,
)

MAX_NAME_LENGTH = 100
MAX_SHORT_TEXT_LENGTH = 200
MAX_LONG_TEXT_LENGTH = 4000
CLIENT_ROLE_EMPLOYEE = 'сотрудник'
CLIENT_ROLE_MANAGER = 'руководитель'
CLIENT_ROLES = (CLIENT_ROLE_EMPLOYEE, CLIENT_ROLE_MANAGER)

_LEAD_FIELDS = (
    'first_name',
    'last_name',
    'middle_name',
    'phone',
    'email',
    'business_info',
    'niche',
    'company_size',
    'business_size',
    'company_volume',
    'demand_volume',
    'tasks',
    'client_role',
    'deadline',
    'task_type',
    'product_interest',
    'budget',
    'contact_method',
    'convenient_time',
    'comment',
)

_FIELD_LABELS = {
    'first_name': 'имя',
    'last_name': 'фамилия',
    'middle_name': 'отчество',
    'business_info': 'информация о бизнесе',
    'niche': 'ниша бизнеса',
    'company_size': 'размер компании',
    'business_size': 'размер бизнеса',
    'company_volume': 'объём',
    'demand_volume': 'объём потребности',
    'tasks': 'задачи',
    'client_role': 'кто заполняет заявку',
    'deadline': 'срок результата',
    'task_type': 'тип задачи',
    'product_interest': 'интересующий продукт',
    'budget': 'бюджет',
    'contact_method': 'способ связи',
    'convenient_time': 'удобное время',
    'comment': 'комментарий',
}

_LONG_FIELDS = frozenset({'business_info', 'tasks', 'comment'})
_OPTIONAL_FIELDS = frozenset({'middle_name', 'comment'})


def prepare_lead(payload: dict[str, object]) -> dict[str, str]:
    """Проверяет анкету и возвращает строки для вставки."""
    prepared: dict[str, str] = {}
    for field in _LEAD_FIELDS:
        if field in ('phone', 'email'):
            continue
        label = _FIELD_LABELS[field]
        if field in _LONG_FIELDS:
            max_length = MAX_LONG_TEXT_LENGTH
        elif field in ('first_name', 'last_name', 'middle_name'):
            max_length = MAX_NAME_LENGTH
        elif field == 'client_role':
            max_length = 32
        else:
            max_length = MAX_SHORT_TEXT_LENGTH
        prepared[field] = clean_text(
            payload.get(field, ''),
            max_length=max_length,
            label=label,
            required=field not in _OPTIONAL_FIELDS,
            single_line=field not in _LONG_FIELDS,
        )

    role = prepared['client_role']
    if role not in CLIENT_ROLES:
        raise AppError(
            'invalid_data',
            'Укажите, кто заполняет заявку: «сотрудник» или «руководитель»',
            400,
            {'field': 'кто заполняет заявку'},
        )

    prepared['phone'] = clean_phone(payload.get('phone', ''))
    prepared['email'] = clean_email(payload.get('email', ''))
    if prepared['phone'] == '' and prepared['email'] == '':
        raise AppError(
            'invalid_data',
            'Укажите телефон или почту',
            400,
            {'field': 'контакт'},
        )
    return prepared


def _insert_sql() -> str:
    """Собирает INSERT. Имена колонок — константа, не данные клиента."""
    columns = ', '.join(assert_identifier(name) for name in _LEAD_FIELDS)
    numbers = ', '.join(f'${index}' for index in range(1, len(_LEAD_FIELDS) + 1))
    return f'INSERT INTO leads ({columns}) VALUES ({numbers}) RETURNING *'


def _update_sql() -> str:
    """Собирает UPDATE. Первым параметром всегда идёт идентификатор."""
    assignments = ', '.join(
        f'{assert_identifier(column)} = ${index}'
        for index, column in enumerate(_LEAD_FIELDS, start=2)
    )
    return (
        f'UPDATE leads SET {assignments}, updated_at = NOW() '
        f'WHERE id = $1 RETURNING *'
    )


def _lead_values(data: dict[str, str]) -> tuple[str, ...]:
    """Возвращает значения в порядке колонок INSERT."""
    return tuple(data[field] for field in _LEAD_FIELDS)


class Lead:
    """Анкета тёплого клиента. Одна строка — одна заявка.

    Бюджет хранится строкой: так его отдаёт ползунок на сайте.
    Размер компании и размер бизнеса, объём и объём потребности
    лежат отдельно: в описании контура это разные ответы формы.

    ```sql
    CREATE TABLE IF NOT EXISTS leads (
        id BIGSERIAL PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        middle_name VARCHAR(100) NOT NULL DEFAULT '',
        phone VARCHAR(32) NOT NULL DEFAULT '',
        email VARCHAR(254) NOT NULL DEFAULT '',
        business_info TEXT NOT NULL,
        niche VARCHAR(200) NOT NULL,
        company_size VARCHAR(200) NOT NULL,
        business_size VARCHAR(200) NOT NULL,
        company_volume VARCHAR(200) NOT NULL,
        demand_volume VARCHAR(200) NOT NULL,
        tasks TEXT NOT NULL,
        client_role VARCHAR(32) NOT NULL,
        deadline VARCHAR(200) NOT NULL,
        task_type VARCHAR(200) NOT NULL,
        product_interest VARCHAR(200) NOT NULL,
        budget VARCHAR(200) NOT NULL,
        contact_method VARCHAR(200) NOT NULL,
        convenient_time VARCHAR(200) NOT NULL,
        comment TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT leads_contact_check CHECK (phone <> '' OR email <> ''),
        CONSTRAINT leads_client_role_check CHECK (
            client_role IN ('сотрудник', 'руководитель')
        ),
        CONSTRAINT leads_required_text_check CHECK (
            first_name <> ''
            AND last_name <> ''
            AND business_info <> ''
            AND niche <> ''
            AND company_size <> ''
            AND business_size <> ''
            AND company_volume <> ''
            AND demand_volume <> ''
            AND tasks <> ''
            AND deadline <> ''
            AND task_type <> ''
            AND product_interest <> ''
            AND budget <> ''
            AND contact_method <> ''
            AND convenient_time <> ''
        ),
        CONSTRAINT leads_text_length_check CHECK (
            char_length(business_info) <= 4000
            AND char_length(tasks) <= 4000
            AND char_length(comment) <= 4000
        )
    );

    CREATE INDEX IF NOT EXISTS leads_created_at_idx
        ON leads (created_at DESC, id DESC);

    COMMENT ON TABLE leads IS
        'Заявка тёплого клиента. Одна строка — одна анкета.';
    COMMENT ON COLUMN leads.budget IS
        'Значение ползунка бюджета, как его прислал сайт, строкой.';
    COMMENT ON COLUMN leads.client_role IS
        'Кто заполняет заявку: сотрудник или руководитель.';
    ```
    """

    table_name = 'leads'
    columns = (
        'id',
        *_LEAD_FIELDS,
        'created_at',
        'updated_at',
    )


class LeadCrud:
    """Создание, чтение, замена и удаление заявки."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def create(self, payload: dict[str, object]) -> dict[str, object]:
        """Вставляет анкету и возвращает строку с новым id."""
        data = prepare_lead(payload)
        try:
            row = await self._database.fetchrow(_insert_sql(), *_lead_values(data))
        except asyncpg.PostgresError as error:
            raise map_postgres_error(error) from None
        if row is None:
            raise AppError('database_error', 'Заявка не сохранилась', 500, None)
        return row

    async def get(self, lead_id: int) -> dict[str, object]:
        """Возвращает одну заявку."""
        row = await self._database.fetchrow(
            'SELECT * FROM leads WHERE id = $1',
            lead_id,
        )
        if row is None:
            raise AppError('not_found', 'Заявка не найдена', 404, None)
        return row

    async def list_all(self, limit: int, offset: int) -> dict[str, object]:
        """Возвращает страницу заявок, новые сверху."""
        rows = await self._database.fetch(
            '''
            SELECT * FROM leads
            ORDER BY created_at DESC, id DESC
            LIMIT $1 OFFSET $2
            ''',
            limit,
            offset,
        )
        total = await self._database.fetchval('SELECT COUNT(*)::int FROM leads')
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
        """Полностью заменяет поля анкеты."""
        data = prepare_lead(payload)
        try:
            row = await self._database.fetchrow(
                _update_sql(),
                lead_id,
                *_lead_values(data),
            )
        except asyncpg.PostgresError as error:
            raise map_postgres_error(error) from None
        if row is None:
            raise AppError('not_found', 'Заявка не найдена', 404, None)
        return row

    async def delete(self, lead_id: int) -> dict[str, object]:
        """Удаляет заявку. Метрики поведения уходят вместе с ней."""
        row = await self._database.fetchrow(
            'DELETE FROM leads WHERE id = $1 RETURNING id',
            lead_id,
        )
        if row is None:
            raise AppError('not_found', 'Заявка не найдена', 404, None)
        return row
