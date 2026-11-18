"""Регистрация первого администратора, вход и проверка сессии."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings
from app.core.responses import success
from app.core.security import create_access_token
from app.models.admin import (
    MAX_LOGIN_LENGTH,
    MAX_PASSWORD_LENGTH,
    AdminCrud,
    public_admin,
)
from app.routes.deps import get_admin_crud, get_settings, require_admin

router = APIRouter(prefix='/auth', tags=['авторизация'])


class AuthBody(BaseModel):
    """Логин и пароль администратора."""

    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    login: str = Field(min_length=3, max_length=MAX_LOGIN_LENGTH)
    password: str = Field(min_length=8, max_length=MAX_PASSWORD_LENGTH)


@router.get('/bootstrap-status')
async def bootstrap_status(
    crud: AdminCrud = Depends(get_admin_crud),
) -> dict[str, object]:
    """Сообщает фронтенду, можно ли показать кнопку регистрации."""
    open_registration = await crud.registration_open()
    return success(
        {'registration_open': open_registration},
        'Статус регистрации получен',
    )


@router.post('/register', status_code=201)
async def register_admin(
    body: AuthBody,
    crud: AdminCrud = Depends(get_admin_crud),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Создаёт первого администратора, пока таблица пуста."""
    row = await crud.create_bootstrap(body.model_dump())
    token = create_access_token(
        subject=str(row['id']),
        secret=settings.jwt_secret,
        expire_minutes=settings.jwt_expire_minutes,
        extra={'login': row['login']},
    )
    return success(
        {
            'access_token': token,
            'token_type': 'Bearer',
            'admin': public_admin(row),
        },
        'Администратор зарегистрирован',
    )


@router.post('/login')
async def login_admin(
    body: AuthBody,
    crud: AdminCrud = Depends(get_admin_crud),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Проверяет пароль и выдаёт JWT."""
    row = await crud.authenticate(body.login, body.password)
    token = create_access_token(
        subject=str(row['id']),
        secret=settings.jwt_secret,
        expire_minutes=settings.jwt_expire_minutes,
        extra={'login': row['login']},
    )
    return success(
        {
            'access_token': token,
            'token_type': 'Bearer',
            'admin': public_admin(row),
        },
        'Вход выполнен',
    )


@router.get('/me')
async def current_admin(
    admin: dict[str, object] = Depends(require_admin),
) -> dict[str, object]:
    """Возвращает профиль по действующему JWT."""
    return success(admin, 'Профиль администратора получен')
