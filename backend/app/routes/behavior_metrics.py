"""Публичный приём живых метрик главной страницы."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict, Field

from app.core.responses import success
from app.models.behavior_metrics import (
    MAX_BUTTONS_CLICKED_LENGTH,
    MAX_CURSOR_POSITIONS_LENGTH,
    MAX_LIST_LIMIT,
    BehaviorMetricsCrud,
)
from app.routes.deps import get_behavior_metrics_crud, require_admin

router = APIRouter(prefix='/behavior-metrics', tags=['живые метрики'])


class BehaviorMetricsBody(BaseModel):
    """Пакет, который главная страница шлёт каждую секунду."""

    model_config = ConfigDict(extra='forbid')

    application_id: int = Field(default=0, ge=0)
    time_on_page: int = Field(default=0, ge=0)
    buttons_clicked: str = Field(default='', max_length=MAX_BUTTONS_CLICKED_LENGTH)
    cursor_positions: str = Field(default='', max_length=MAX_CURSOR_POSITIONS_LENGTH)
    return_frequency: int = Field(default=0, ge=0)


@router.post('/', status_code=201)
@router.post('', status_code=201)
async def create_behavior_metrics(
    body: BehaviorMetricsBody,
    crud: BehaviorMetricsCrud = Depends(get_behavior_metrics_crud),
) -> dict[str, object]:
    """Принимает снимок метрик с главной страницы."""
    row = await crud.create(body.model_dump())
    return success(row, 'Метрики сохранены')


@router.get('/')
@router.get('')
async def list_behavior_metrics(
    _admin: dict[str, object] = Depends(require_admin),
    limit: int = Query(default=100, ge=1, le=MAX_LIST_LIMIT),
    offset: int = Query(default=0, ge=0, le=100_000),
    skip: int | None = Query(default=None, ge=0, le=100_000),
    crud: BehaviorMetricsCrud = Depends(get_behavior_metrics_crud),
) -> dict[str, object]:
    """Список снимков для администратора. skip — синоним offset."""
    page_offset = offset if skip is None else skip
    page = await crud.list_all(limit, page_offset)
    return success(page, 'Список метрик получен')


@router.get('/{metrics_id}')
async def read_behavior_metrics(
    _admin: dict[str, object] = Depends(require_admin),
    metrics_id: int = Path(ge=1),
    crud: BehaviorMetricsCrud = Depends(get_behavior_metrics_crud),
) -> dict[str, object]:
    """Один снимок метрик."""
    row = await crud.get(metrics_id)
    return success(row, 'Метрики получены')
