"""Создание таблиц из SQL, записанного в докстринге модели."""

from __future__ import annotations

import textwrap

from app.core.database import Database
from app.models import MODEL_CLASSES


def extract_table_sql(model: type) -> str:
    """Достаёт блок ```sql из докстринга класса модели."""
    document = model.__doc__
    if document is None or document.strip() == '':
        raise RuntimeError(f'У модели {model.__name__} нет докстринга с SQL')
    marker = '```sql'
    start = document.find(marker)
    if start < 0:
        raise RuntimeError(f'В докстринге {model.__name__} нет блока SQL')
    body_start = start + len(marker)
    end = document.find('```', body_start)
    if end < 0:
        raise RuntimeError(f'Блок SQL в {model.__name__} не закрыт')
    sql = textwrap.dedent(document[body_start:end]).strip()
    if 'CREATE TABLE' not in sql.upper():
        raise RuntimeError(f'В докстринге {model.__name__} нет CREATE TABLE')
    return sql


def split_sql(sql: str) -> list[str]:
    """Делит скрипт по точкам с запятой, не трогая кавычки."""
    parts: list[str] = []
    current: list[str] = []
    in_single = False
    index = 0
    while index < len(sql):
        char = sql[index]
        if char == "'":
            if in_single and index + 1 < len(sql) and sql[index + 1] == "'":
                current.append("''")
                index += 2
                continue
            in_single = not in_single
            current.append(char)
        elif char == ';' and not in_single:
            statement = ''.join(current).strip()
            if statement:
                parts.append(statement)
            current = []
        else:
            current.append(char)
        index += 1
    tail = ''.join(current).strip()
    if tail:
        parts.append(tail)
    return parts


async def apply_schema(database: Database) -> None:
    """Создаёт таблицы в порядке зависимостей, если их ещё нет."""
    for model in MODEL_CLASSES:
        for statement in split_sql(extract_table_sql(model)):
            await database.execute(statement)
