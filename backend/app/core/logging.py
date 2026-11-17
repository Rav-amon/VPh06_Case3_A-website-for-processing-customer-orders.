"""Структурный журнал без текста заявок и паролей."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger('leads')


def configure_logging() -> None:
    """Включает одну строку JSON на событие приложения."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')


def log_event(
    level: int,
    message: str,
    context: dict[str, object] | None = None,
) -> None:
    """Пишет уровень, сообщение и короткий контекст."""
    payload = {
        'level': logging.getLevelName(level).lower(),
        'message': message,
        'context': context or {},
    }
    logger.log(level, json.dumps(payload, ensure_ascii=False))
