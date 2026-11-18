"""Маршруты заявки. Создание публичное, остальное — по JWT."""

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict, Field

from app.core.responses import success
from app.models.lead import (
    MAX_LONG_TEXT_LENGTH,
    MAX_NAME_LENGTH,
    MAX_SHORT_TEXT_LENGTH,
    LeadCrud,
)
from app.routes.deps import get_lead_crud, require_admin

DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 100
MAX_OFFSET = 100_000

router = APIRouter(prefix='/leads', tags=['заявки'])


class LeadBody(BaseModel):
    """Поля анкеты, которые заполняет тёплый клиент."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    first_name: str = Field(max_length=MAX_NAME_LENGTH)
    last_name: str = Field(max_length=MAX_NAME_LENGTH)
    middle_name: str = Field(default='', max_length=MAX_NAME_LENGTH)
    phone: str = Field(default='', max_length=32)
    email: str = Field(default='', max_length=254)
    business_info: str = Field(max_length=MAX_LONG_TEXT_LENGTH)
    niche: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    company_size: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    business_size: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    company_volume: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    demand_volume: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    tasks: str = Field(max_length=MAX_LONG_TEXT_LENGTH)
    client_role: str = Field(max_length=32)
    deadline: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    task_type: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    product_interest: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    budget: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    contact_method: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    convenient_time: str = Field(max_length=MAX_SHORT_TEXT_LENGTH)
    comment: str = Field(default='', max_length=MAX_LONG_TEXT_LENGTH)


@router.post('', status_code=201)
async def create_lead(
    body: LeadBody,
    crud: LeadCrud = Depends(get_lead_crud),
) -> dict[str, object]:
    """Сохраняет заявку."""
    row = await crud.create(body.model_dump())
    return success(row, 'Заявка сохранена')


@router.get('')
async def list_leads(
    _admin: dict[str, object] = Depends(require_admin),
    limit: int = Query(default=DEFAULT_LIST_LIMIT, ge=1, le=MAX_LIST_LIMIT),
    offset: int = Query(default=0, ge=0, le=MAX_OFFSET),
    crud: LeadCrud = Depends(get_lead_crud),
) -> dict[str, object]:
    """Возвращает страницу заявок."""
    page = await crud.list_all(limit, offset)
    return success(page, 'Список заявок получен')


@router.get('/{lead_id}')
async def read_lead(
    _admin: dict[str, object] = Depends(require_admin),
    lead_id: int = Path(ge=1),
    crud: LeadCrud = Depends(get_lead_crud),
) -> dict[str, object]:
    """Возвращает одну заявку."""
    row = await crud.get(lead_id)
    return success(row, 'Заявка получена')


@router.put('/{lead_id}')
async def update_lead(
    body: LeadBody,
    _admin: dict[str, object] = Depends(require_admin),
    lead_id: int = Path(ge=1),
    crud: LeadCrud = Depends(get_lead_crud),
) -> dict[str, object]:
    """Заменяет поля заявки."""
    row = await crud.update(lead_id, body.model_dump())
    return success(row, 'Заявка обновлена')


@router.delete('/{lead_id}')
async def delete_lead(
    _admin: dict[str, object] = Depends(require_admin),
    lead_id: int = Path(ge=1),
    crud: LeadCrud = Depends(get_lead_crud),
) -> dict[str, object]:
    """Удаляет заявку и связанные метрики."""
    row = await crud.delete(lead_id)
    return success(row, 'Заявка удалена')
