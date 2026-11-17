"""Модели таблиц. Порядок важен: заявка создаётся раньше метрик."""

from app.models.admin_settings import AdminSettings
from app.models.behavior import LeadBehavior
from app.models.lead import Lead

MODEL_CLASSES = (Lead, LeadBehavior, AdminSettings)
