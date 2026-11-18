"""Учётные записи администраторов панели и операции с ними."""

from __future__ import annotations

import re

import asyncpg

from app.core.database import Database
from app.core.errors import AppError, map_postgres_error
from app.core.security import hash_password, verify_password
from app.core.text import clean_text

MAX_LOGIN_LENGTH = 64
MIN_LOGIN_LENGTH = 3
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

_LOGIN = re.compile(r'^[a-zA-Z0-9._-]+$')


def prepare_admin_credentials(payload: dict[str, object]) -> dict[str, str]:
    """Проверяет логин и пароль перед регистрацией или сменой."""
    login = clean_text(
        payload.get('login', ''),
        max_length=MAX_LOGIN_LENGTH,
        label='логин',
        required=True,
        single_line=True,
    ).lower()
    if len(login) < MIN_LOGIN_LENGTH:
        raise AppError(
            'invalid_data',
            f'Логин короче {MIN_LOGIN_LENGTH} символов',
            400,
            {'field': 'логин'},
        )
    if _LOGIN.fullmatch(login) is None:
        raise AppError(
            'invalid_data',
            'Логин может содержать латинские буквы, цифры, точку, дефис и подчёркивание',
            400,
            {'field': 'логин'},
        )
    password = payload.get('password', '')
    if not isinstance(password, str):
        raise AppError(
            'invalid_data',
            '«пароль» должно быть строкой',
            400,
            {'field': 'пароль'},
        )
    if '\x00' in password:
        raise AppError(
            'invalid_data',
            'Пароль содержит недопустимые символы',
            400,
            {'field': 'пароль'},
        )
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AppError(
            'invalid_data',
            f'Пароль короче {MIN_PASSWORD_LENGTH} символов',
            400,
            {'field': 'пароль'},
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise AppError(
            'invalid_data',
            f'Пароль длиннее {MAX_PASSWORD_LENGTH} символов',
            400,
            {'field': 'пароль'},
        )
    return {
        'login': login,
        'password_hash': hash_password(password),
    }


def public_admin(row: dict[str, object]) -> dict[str, object]:
    """Убирает хэш пароля из ответа API."""
    return {
        'id': row['id'],
        'login': row['login'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
    }


class Admin:
    """Администратор панели. Первая запись открывает регистрацию только один раз.

    ```sql
    CREATE TABLE IF NOT EXISTS admins (
        id BIGSERIAL PRIMARY KEY,
        login VARCHAR(64) NOT NULL,
        password_hash VARCHAR(128) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT admins_login_unique UNIQUE (login),
        CONSTRAINT admins_login_check CHECK (
            char_length(login) >= 3
            AND char_length(login) <= 64
            AND login = lower(login)
            AND login ~ '^[a-z0-9._-]+$'
        ),
        CONSTRAINT admins_password_hash_check CHECK (
            password_hash <> ''
            AND char_length(password_hash) <= 128
        )
    );

    CREATE INDEX IF NOT EXISTS admins_login_idx ON admins (login);

    COMMENT ON TABLE admins IS
        'Учётные записи администраторов панели Autéllo.';
    COMMENT ON COLUMN admins.login IS
        'Уникальный логин в нижнем регистре.';
    COMMENT ON COLUMN admins.password_hash IS
        'Bcrypt-хэш пароля. В API не отдаётся.';
    ```
    """

    table_name = 'admins'
    columns = (
        'id',
        'login',
        'password_hash',
        'created_at',
        'updated_at',
    )


class AdminCrud:
    """Создание, чтение и проверка администраторов."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def count(self) -> int:
        """Считает число администраторов в базе."""
        total = await self._database.fetchval('SELECT COUNT(*)::int FROM admins')
        return int(total or 0)

    async def registration_open(self) -> bool:
        """Регистрация доступна, пока в базе нет ни одного администратора."""
        return await self.count() == 0

    async def create(self, payload: dict[str, object]) -> dict[str, object]:
        """Создаёт администратора. Повторный логин даёт конфликт."""
        data = prepare_admin_credentials(payload)
        try:
            row = await self._database.fetchrow(
                '''
                INSERT INTO admins (login, password_hash)
                VALUES ($1, $2)
                RETURNING *
                ''',
                data['login'],
                data['password_hash'],
            )
        except asyncpg.PostgresError as error:
            raise map_postgres_error(error) from None
        if row is None:
            raise AppError(
                'database_error',
                'Администратор не сохранился',
                500,
                None,
            )
        return row

    async def create_bootstrap(self, payload: dict[str, object]) -> dict[str, object]:
        """Создаёт первого администратора и блокирует повторную регистрацию."""
        if not await self.registration_open():
            raise AppError(
                'forbidden',
                'Регистрация закрыта: администратор уже существует',
                403,
                None,
            )
        return await self.create(payload)

    async def get(self, admin_id: int) -> dict[str, object]:
        """Возвращает одного администратора по id."""
        row = await self._database.fetchrow(
            'SELECT * FROM admins WHERE id = $1',
            admin_id,
        )
        if row is None:
            raise AppError('not_found', 'Администратор не найден', 404, None)
        return row

    async def get_by_login(self, login: str) -> dict[str, object] | None:
        """Ищет администратора по логину без ошибки 404."""
        cleaned = clean_text(
            login,
            max_length=MAX_LOGIN_LENGTH,
            label='логин',
            required=True,
            single_line=True,
        ).lower()
        return await self._database.fetchrow(
            'SELECT * FROM admins WHERE login = $1',
            cleaned,
        )

    async def list_all(self) -> dict[str, object]:
        """Возвращает список администраторов без хэшей паролей."""
        rows = await self._database.fetch(
            'SELECT id, login, created_at, updated_at FROM admins ORDER BY id'
        )
        return {'items': rows, 'total': len(rows)}

    async def authenticate(
        self,
        login: str,
        password: str,
    ) -> dict[str, object]:
        """Проверяет логин и пароль. При ошибке не раскрывает, чего не хватило."""
        if not isinstance(password, str) or password == '':
            raise AppError(
                'unauthorized',
                'Неверный логин или пароль',
                401,
                None,
            )
        row = await self.get_by_login(login)
        if row is None:
            raise AppError(
                'unauthorized',
                'Неверный логин или пароль',
                401,
                None,
            )
        password_hash = row.get('password_hash', '')
        if not isinstance(password_hash, str):
            raise AppError(
                'unauthorized',
                'Неверный логин или пароль',
                401,
                None,
            )
        if not verify_password(password, password_hash):
            raise AppError(
                'unauthorized',
                'Неверный логин или пароль',
                401,
                None,
            )
        return row

    async def delete(self, admin_id: int) -> dict[str, object]:
        """Удаляет администратора по id."""
        row = await self._database.fetchrow(
            'DELETE FROM admins WHERE id = $1 RETURNING id, login',
            admin_id,
        )
        if row is None:
            raise AppError('not_found', 'Администратор не найден', 404, None)
        return row
