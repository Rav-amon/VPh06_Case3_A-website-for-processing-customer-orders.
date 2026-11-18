"""Сводная статистика для панели администратора."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.responses import success
from app.models.stats import StatsCrud
from app.routes.deps import get_stats_crud, require_admin

router = APIRouter(prefix='/stats', tags=['статистика'])


@router.get('')
async def read_stats(
    _admin: dict[str, object] = Depends(require_admin),
    crud: StatsCrud = Depends(get_stats_crud),
) -> dict[str, object]:
    """Отдаёт агрегаты по заявкам и поведению."""
    data = await crud.overview()
    return success(data, 'Статистика получена')
