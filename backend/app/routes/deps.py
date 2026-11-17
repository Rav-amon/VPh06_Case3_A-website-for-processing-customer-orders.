"""Зависимости маршрутов: драйвер базы и классы операций."""

from fastapi import Depends, Request

from app.core.database import Database
from app.models.admin_settings import AdminSettingsCrud
from app.models.behavior import LeadBehaviorCrud
from app.models.lead import LeadCrud


def get_database(request: Request) -> Database:
    """Возвращает драйвер, открытый при старте приложения."""
    return request.app.state.database


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
