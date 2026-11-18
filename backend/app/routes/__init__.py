"""Общий роутер. К нему подключаются роуты всех моделей."""

from fastapi import APIRouter

from app.routes.admin_settings import router as admin_settings_router
from app.routes.auth import router as auth_router
from app.routes.behavior import router as behavior_router
from app.routes.health import router as health_router
from app.routes.lead import router as lead_router
from app.routes.stats import router as stats_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(lead_router)
api_router.include_router(behavior_router)
api_router.include_router(admin_settings_router)
api_router.include_router(stats_router)
api_router.include_router(health_router)
