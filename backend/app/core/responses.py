"""Обёртка успешного ответа: data, error, message."""

from __future__ import annotations

import json
from typing import cast

from starlette.responses import JSONResponse

from app.core.errors import AppError


def success(data: object, message: str) -> dict[str, object]:
    """Собирает успешный ответ."""
    return {'data': data, 'error': None, 'message': message}


def failure(error: AppError) -> dict[str, object]:
    """Собирает ответ ошибки в том же конверте, что и успешный."""
    return {
        'data': None,
        'error': {
            'code': error.code,
            'message': error.message,
            'details': error.details,
        },
        'message': error.message,
    }


class Utf8JSONResponse(JSONResponse):
    """JSON с русским текстом без экранирования в \\uXXXX."""

    media_type = 'application/json; charset=utf-8'

    def render(self, content: object) -> bytes:
        return json.dumps(
            cast(object, content),
            ensure_ascii=False,
        ).encode('utf-8')
