"""Единый формат ошибки API: code, message, details."""

from __future__ import annotations

import asyncpg


class AppError(Exception):
    """Ошибка, которую маршрут отдаёт клиенту без текста SQL."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: object = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def map_postgres_error(error: asyncpg.PostgresError) -> AppError:
    """Переводит ограничение базы в ответ без значений из запроса."""
    if isinstance(error, asyncpg.UniqueViolationError):
        constraint = getattr(error, 'constraint_name', '')
        if constraint == 'lead_behavior_pkey':
            return AppError(
                'conflict',
                'Метрики для этой заявки уже сохранены',
                409,
                None,
            )
        if constraint == 'admin_settings_pkey':
            return AppError('conflict', 'Настройки уже созданы', 409, None)
        if constraint == 'admins_login_unique':
            return AppError(
                'conflict',
                'Администратор с таким логином уже существует',
                409,
                None,
            )
        return AppError('conflict', 'Запись уже существует', 409, None)
    if isinstance(error, asyncpg.ForeignKeyViolationError):
        return AppError('not_found', 'Связанная заявка не найдена', 404, None)
    if isinstance(error, asyncpg.CheckViolationError):
        return AppError(
            'invalid_data',
            'Данные не проходят ограничения таблицы',
            400,
            None,
        )
    return AppError('database_error', 'Не удалось обработать данные', 500, None)
