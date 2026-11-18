"""Очередь заявок с интеллектуальным скорингом температуры."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query

from app.core.lead_intelligence import (
    enrich_lead,
    sort_leads_by_temperature,
    summarize_intelligence,
)
from app.core.responses import success
from app.models.lead import LeadCrud
from app.routes.deps import get_lead_crud, require_admin

MAX_LIST_LIMIT = 100
MAX_OFFSET = 100_000
# Берём запас строк, чтобы после скоринга отдать нужную страницу уже отсортированной.
FETCH_CAP = 500

router = APIRouter(prefix='/applications', tags=['заявки-очередь'])


@router.get('/')
@router.get('')
async def list_applications(
    _admin: dict[str, object] = Depends(require_admin),
    limit: int = Query(default=100, ge=1, le=MAX_LIST_LIMIT),
    offset: int = Query(default=0, ge=0, le=MAX_OFFSET),
    skip: int | None = Query(default=None, ge=0, le=MAX_OFFSET),
    crud: LeadCrud = Depends(get_lead_crud),
) -> dict[str, object]:
    """Список заявок с температурой. Горячие выше холодных."""
    page_offset = offset if skip is None else skip
    raw = await crud.list_all(FETCH_CAP, 0)
    items_raw = raw.get('items', [])
    if not isinstance(items_raw, list):
        items_raw = []
    ranked = sort_leads_by_temperature(list(items_raw))
    total = int(raw.get('total', len(ranked)) or 0)
    page_items = ranked[page_offset: page_offset + limit]
    summary = summarize_intelligence(ranked)
    return success(
        {
            'items': page_items,
            'total': total,
            'limit': limit,
            'offset': page_offset,
            'skip': page_offset,
            'summary': summary,
        },
        'Очередь заявок получена',
    )


@router.get('/{application_id}')
async def read_application(
    _admin: dict[str, object] = Depends(require_admin),
    application_id: int = Path(ge=1),
    crud: LeadCrud = Depends(get_lead_crud),
) -> dict[str, object]:
    """Одна заявка с блоком intelligence."""
    row = await crud.get(application_id)
    return success(enrich_lead(row), 'Заявка получена')
