"""Зависимости маршрутов: драйвер базы, CRUD и проверка JWT."""

from __future__ import annotations

from fastapi import Depends, Request

from app.core.config import Settings, load_settings
from app.core.database import Database
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models.admin import AdminCrud, public_admin
from app.models.admin_settings import AdminSettingsCrud
from app.models.behavior import LeadBehaviorCrud
from app.models.behavior_metrics import BehaviorMetricsCrud
from app.models.lead import LeadCrud
from app.models.stats import StatsCrud


def get_database(request: Request) -> Database:
    """Возвращает драйвер, открытый при старте приложения."""
    return request.app.state.database


def get_settings(request: Request) -> Settings:
    """Возвращает настройки, загруженные при старте приложения."""
    settings = getattr(request.app.state, 'settings', None)
    if isinstance(settings, Settings):
        return settings
    return load_settings()


def get_lead_crud(database: Database = Depends(get_database)) -> LeadCrud:
    """Собирает операции заявки поверх текущего драйвера."""
    return LeadCrud(database)


def get_behavior_crud(
    database: Database = Depends(get_database),
) -> LeadBehaviorCrud:
    """Собирает операции метрик поверх текущего драйвера."""
    return LeadBehaviorCrud(database)


def get_admin_settings_crud(
    database: Database = Depends(get_database),
) -> AdminSettingsCrud:
    """Собирает операции настроек поверх текущего драйвера."""
    return AdminSettingsCrud(database)


def get_admin_crud(database: Database = Depends(get_database)) -> AdminCrud:
    """Собирает операции администраторов поверх текущего драйвера."""
    return AdminCrud(database)


def get_stats_crud(database: Database = Depends(get_database)) -> StatsCrud:
    """Собирает агрегаты статистики поверх текущего драйвера."""
    return StatsCrud(database)


def get_behavior_metrics_crud(
    database: Database = Depends(get_database),
) -> BehaviorMetricsCrud:
    """Собирает операции живых метрик поверх текущего драйвера."""
    return BehaviorMetricsCrud(database)


def _bearer_token(request: Request) -> str:
    """Достаёт Bearer-токен из заголовка Authorization."""
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        raise AppError(
            'unauthorized',
            'Нужен токен доступа администратора',
            401,
            None,
        )
    token = header[7:].strip()
    if token == '':
        raise AppError(
            'unauthorized',
            'Нужен токен доступа администратора',
            401,
            None,
        )
    return token


async def require_admin(
    request: Request,
    crud: AdminCrud = Depends(get_admin_crud),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Проверяет JWT и возвращает публичный профиль администратора."""
    token = _bearer_token(request)
    payload = decode_access_token(token, settings.jwt_secret)
    subject = str(payload['sub'])
    if not subject.isdigit():
        raise AppError(
            'unauthorized',
            'Токен доступа недействителен',
            401,
            None,
        )
    row = await crud.get(int(subject))
    return public_admin(row)
