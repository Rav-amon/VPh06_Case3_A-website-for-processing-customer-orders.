"""Точка входа. Подключает общий роутер и открывает пул базы."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app.core.database import Database
from app.core.errors import AppError
from app.core.logging import configure_logging, log_event
from app.core.responses import Utf8JSONResponse, failure
from app.core.schema import apply_schema
from app.models.admin_settings import AdminSettingsCrud
from app.routes import api_router
from app.routes.applications import router as applications_router
from app.routes.behavior_metrics import router as behavior_metrics_router

API_PREFIX = '/api/v1'


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Подключается к базе, создаёт таблицы и закрывает пул при остановке."""
    from app.core.config import load_settings

    configure_logging()
    settings = load_settings()
    database = await Database.connect(settings)
    app.state.settings = settings
    app.state.database = database
    try:
        await apply_schema(database)
        await AdminSettingsCrud(database).ensure_defaults()
        log_event(logging.INFO, 'схема базы проверена', {})
        yield
    finally:
        await database.close()


app = FastAPI(
    title='Autéllo Barskiy',
    summary='Приватный API. Доступен только через Nginx во внутренней сети.',
    version='1.0.0',
    lifespan=lifespan,
    default_response_class=Utf8JSONResponse,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(api_router, prefix=API_PREFIX)
app.include_router(behavior_metrics_router, prefix='/api')
app.include_router(applications_router, prefix='/api')


def _validation_details(errors: list[object]) -> list[dict[str, str]]:
    """Оставляет поле и текст проверки, без присланных персональных данных."""
    details: list[dict[str, str]] = []
    for item in errors:
        if not isinstance(item, dict):
            continue
        location = item.get('loc', ())
        field = '.'.join(str(part) for part in location)
        message = item.get('msg', '')
        details.append({
            'field': field,
            'message': message if isinstance(message, str) else '',
        })
    return details


@app.exception_handler(AppError)
async def handle_app_error(
    request: Request,
    error: AppError,
) -> Utf8JSONResponse:
    """Отдаёт ошибку приложения в общем конверте."""
    return Utf8JSONResponse(status_code=error.status_code, content=failure(error))


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request,
    error: RequestValidationError,
) -> Utf8JSONResponse:
    """Переводит ошибку схемы запроса в общий конверт."""
    app_error = AppError(
        'validation_error',
        'Проверьте поля запроса',
        422,
        _validation_details(list(error.errors())),
    )
    return Utf8JSONResponse(status_code=422, content=failure(app_error))


@app.exception_handler(HTTPException)
async def handle_http_error(
    request: Request,
    error: HTTPException,
) -> Utf8JSONResponse:
    """Переводит пропущенный адрес в общий конверт."""
    message = error.detail if isinstance(error.detail, str) else 'Запрос отклонён'
    app_error = AppError('http_error', message, error.status_code, None)
    return Utf8JSONResponse(status_code=error.status_code, content=failure(app_error))


@app.exception_handler(Exception)
async def handle_unexpected_error(
    request: Request,
    error: Exception,
) -> Utf8JSONResponse:
    """Скрывает внутреннюю ошибку и пишет в журнал только её тип."""
    log_event(
        logging.ERROR,
        'необработанная ошибка',
        {'error_type': type(error).__name__},
    )
    app_error = AppError(
        'internal_error',
        'Не удалось обработать запрос',
        500,
        None,
    )
    return Utf8JSONResponse(status_code=500, content=failure(app_error))
