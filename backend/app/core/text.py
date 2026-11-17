"""Чистые проверки строк. Одинаковый вход даёт одинаковый результат."""

from __future__ import annotations

import re

from app.core.errors import AppError

_PHONE = re.compile(r'^[0-9+()\-\s]{5,32}$')
_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_IDENTIFIER = re.compile(r'^[a-z_][a-z0-9_]*$')


def assert_identifier(name: str) -> str:
    """Пропускает только заранее известное имя колонки."""
    if _IDENTIFIER.fullmatch(name) is None:
        raise RuntimeError('Недопустимое имя колонки')
    return name


def clean_text(
    value: object,
    *,
    max_length: int,
    label: str,
    required: bool,
    single_line: bool,
) -> str:
    """Обрезает пробелы по краям и отвергает пустое обязательное поле."""
    if not isinstance(value, str):
        raise AppError(
            'invalid_data',
            f'«{label}» должно быть строкой',
            400,
            {'field': label},
        )
    cleaned = value.replace('\x00', '').strip()
    if single_line and ('\n' in cleaned or '\r' in cleaned):
        raise AppError(
            'invalid_data',
            f'«{label}» должно быть одной строкой',
            400,
            {'field': label},
        )
    if required and cleaned == '':
        raise AppError(
            'invalid_data',
            f'Заполните поле «{label}»',
            400,
            {'field': label},
        )
    if len(cleaned) > max_length:
        raise AppError(
            'invalid_data',
            f'«{label}» длиннее {max_length} символов',
            400,
            {'field': label},
        )
    return cleaned


def clean_phone(value: object) -> str:
    """Проверяет телефон. Пустая строка значит, что телефон не указан."""
    cleaned = clean_text(
        value,
        max_length=32,
        label='телефон',
        required=False,
        single_line=True,
    )
    if cleaned == '':
        return ''
    if _PHONE.fullmatch(cleaned) is None:
        raise AppError(
            'invalid_data',
            'Телефон может содержать цифры, пробелы и символы +()-',
            400,
            {'field': 'телефон'},
        )
    return cleaned


def clean_email(value: object) -> str:
    """Приводит почту к нижнему регистру. Пустая строка допустима."""
    cleaned = clean_text(
        value,
        max_length=254,
        label='почта',
        required=False,
        single_line=True,
    )
    if cleaned == '':
        return ''
    lowered = cleaned.lower()
    if _EMAIL.fullmatch(lowered) is None:
        raise AppError(
            'invalid_data',
            'Укажите почту в виде имя@домен',
            400,
            {'field': 'почта'},
        )
    return lowered


def require_int(
    value: object,
    *,
    label: str,
    minimum: int,
    maximum: int,
) -> int:
    """Принимает целое число в заданных границах. Логическое значение не подходит."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise AppError(
            'invalid_data',
            f'«{label}» должно быть целым числом',
            400,
            {'field': label},
        )
    if value < minimum or value > maximum:
        raise AppError(
            'invalid_data',
            f'«{label}» должно быть от {minimum} до {maximum}',
            400,
            {'field': label},
        )
    return value
