"""Маршруты метрик. Каждый вызывает только операции LeadBehaviorCrud."""

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict, Field

from app.core.responses import success
from app.models.behavior import (
    MAX_BEHAVIOR_EVENTS,
    MAX_BUTTON_NAME_LENGTH,
    MAX_REFERRER_LENGTH,
    MAX_SCREEN_LENGTH,
    MAX_SELECTOR_LENGTH,
    MAX_TIMEZONE_LENGTH,
    MAX_USER_AGENT_LENGTH,
)
from app.models.behavior import LeadBehaviorCrud
from app.routes.deps import get_behavior_crud

DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 100
MAX_OFFSET = 100_000
MAX_LANGUAGE_LENGTH = 32

router = APIRouter(prefix='/behavior', tags=['метрики'])


class ButtonClickBody(BaseModel):
    """Одна кнопка и сколько раз её нажали."""

    model_config = ConfigDict(extra='forbid')

    name: str = Field(max_length=MAX_BUTTON_NAME_LENGTH)
    count: int = Field(ge=0)


class CursorHotspotBody(BaseModel):
    """Место, где курсор задержался."""

    model_config = ConfigDict(extra='forbid')

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    duration_ms: int = Field(ge=0)
    selector: str = Field(default='', max_length=MAX_SELECTOR_LENGTH)


class BehaviorBody(BaseModel):
    """Пакет поведения, привязанный к уже созданной заявке."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    lead_id: int = Field(ge=1)
    time_on_page_ms: int = Field(ge=0)
    button_clicks: list[ButtonClickBody] = Field(
        default_factory=list,
        max_length=MAX_BEHAVIOR_EVENTS,
    )
    cursor_hotspots: list[CursorHotspotBody] = Field(
        default_factory=list,
        max_length=MAX_BEHAVIOR_EVENTS,
    )
    return_count: int = Field(ge=0)
    user_agent: str = Field(default='', max_length=MAX_USER_AGENT_LENGTH)
    language: str = Field(default='', max_length=MAX_LANGUAGE_LENGTH)
    timezone: str = Field(default='', max_length=MAX_TIMEZONE_LENGTH)
    screen: str = Field(default='', max_length=MAX_SCREEN_LENGTH)
    referrer: str = Field(default='', max_length=MAX_REFERRER_LENGTH)


class BehaviorUpdateBody(BaseModel):
    """Новый пакет метрик. Идентификатор заявки берётся из адреса."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    time_on_page_ms: int = Field(ge=0)
    button_clicks: list[ButtonClickBody] = Field(
        default_factory=list,
        max_length=MAX_BEHAVIOR_EVENTS,
    )
    cursor_hotspots: list[CursorHotspotBody] = Field(
        default_factory=list,
        max_length=MAX_BEHAVIOR_EVENTS,
    )
    return_count: int = Field(ge=0)
    user_agent: str = Field(default='', max_length=MAX_USER_AGENT_LENGTH)
    language: str = Field(default='', max_length=MAX_LANGUAGE_LENGTH)
    timezone: str = Field(default='', max_length=MAX_TIMEZONE_LENGTH)
    screen: str = Field(default='', max_length=MAX_SCREEN_LENGTH)
    referrer: str = Field(default='', max_length=MAX_REFERRER_LENGTH)


@router.post('', status_code=201)
async def create_behavior(
    body: BehaviorBody,
    crud: LeadBehaviorCrud = Depends(get_behavior_crud),
) -> dict[str, object]:
    """Сохраняет метрики для заявки."""
    row = await crud.create(body.model_dump())
    return success(row, 'Метрики сохранены')


@router.get('')
async def list_behavior(
    limit: int = Query(default=DEFAULT_LIST_LIMIT, ge=1, le=MAX_LIST_LIMIT),
    offset: int = Query(default=0, ge=0, le=MAX_OFFSET),
    crud: LeadBehaviorCrud = Depends(get_behavior_crud),
) -> dict[str, object]:
    """Возвращает страницу метрик."""
    page = await crud.list_all(limit, offset)
    return success(page, 'Список метрик получен')


@router.get('/{lead_id}')
async def read_behavior(
    lead_id: int = Path(ge=1),
    crud: LeadBehaviorCrud = Depends(get_behavior_crud),
) -> dict[str, object]:
    """Возвращает метрики одной заявки."""
    row = await crud.get(lead_id)
    return success(row, 'Метрики получены')


@router.put('/{lead_id}')
async def update_behavior(
    body: BehaviorUpdateBody,
    lead_id: int = Path(ge=1),
    crud: LeadBehaviorCrud = Depends(get_behavior_crud),
) -> dict[str, object]:
    """Заменяет метрики заявки."""
    row = await crud.update(lead_id, body.model_dump())
    return success(row, 'Метрики обновлены')


@router.delete('/{lead_id}')
async def delete_behavior(
    lead_id: int = Path(ge=1),
    crud: LeadBehaviorCrud = Depends(get_behavior_crud),
) -> dict[str, object]:
    """Удаляет метрики и оставляет заявку."""
    row = await crud.delete(lead_id)
    return success(row, 'Метрики удалены')
