"""Маршруты настроек интерфейса. Чтение публичное, правки — по JWT."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.core.responses import success
from app.models.admin_settings import (
    MAX_SERVICE_DESCRIPTION_LENGTH,
    MAX_SERVICE_TITLE_LENGTH,
    MAX_SERVICES,
    AdminSettingsCrud,
)
from app.routes.deps import get_admin_settings_crud, require_admin

router = APIRouter(prefix='/admin-settings', tags=['настройки'])


class ServiceBody(BaseModel):
    """Услуга с собственным диапазоном цены для формы."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    code: str = Field(max_length=64)
    title: str = Field(max_length=MAX_SERVICE_TITLE_LENGTH)
    description: str = Field(default='', max_length=MAX_SERVICE_DESCRIPTION_LENGTH)
    price_min: int = Field(ge=0)
    price_max: int = Field(ge=0)
    is_active: bool = True


class AdminSettingsBody(BaseModel):
    """Услуги и края ползунка бюджета."""

    model_config = ConfigDict(extra='forbid')

    services: list[ServiceBody] = Field(default_factory=list, max_length=MAX_SERVICES)
    budget_min: int = Field(ge=0)
    budget_max: int = Field(ge=0)
    budget_step: int = Field(ge=1)


@router.post('', status_code=201)
async def create_admin_settings(
    body: AdminSettingsBody,
    _admin: dict[str, object] = Depends(require_admin),
    crud: AdminSettingsCrud = Depends(get_admin_settings_crud),
) -> dict[str, object]:
    """Создаёт строку настроек, если её ещё нет."""
    row = await crud.create(body.model_dump())
    return success(row, 'Настройки сохранены')


@router.get('')
async def read_admin_settings(
    crud: AdminSettingsCrud = Depends(get_admin_settings_crud),
) -> dict[str, object]:
    """Отдаёт услуги и диапазон бюджета для построения формы."""
    row = await crud.get()
    return success(row, 'Настройки получены')


@router.put('')
async def update_admin_settings(
    body: AdminSettingsBody,
    _admin: dict[str, object] = Depends(require_admin),
    crud: AdminSettingsCrud = Depends(get_admin_settings_crud),
) -> dict[str, object]:
    """Заменяет услуги и диапазон бюджета."""
    row = await crud.update(body.model_dump())
    return success(row, 'Настройки обновлены')


@router.delete('')
async def reset_admin_settings(
    _admin: dict[str, object] = Depends(require_admin),
    crud: AdminSettingsCrud = Depends(get_admin_settings_crud),
) -> dict[str, object]:
    """Возвращает пустой список услуг и диапазон по умолчанию."""
    row = await crud.delete()
    return success(row, 'Настройки сброшены')
