"""Проверки анкеты, метрик и SQL из докстрингов. База не нужна."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.errors import AppError
from app.core.schema import extract_table_sql, split_sql
from app.models import MODEL_CLASSES
from app.models.admin_settings import prepare_admin_settings
from app.models.behavior import prepare_behavior
from app.models.lead import prepare_lead


def lead_payload() -> dict[str, object]:
    """Возвращает полную корректную анкету."""
    return {
        'first_name': 'Иван',
        'last_name': 'Петров',
        'middle_name': 'Сергеевич',
        'phone': '+7 900 000-00-00',
        'email': 'Ivan@Example.com',
        'business_info': 'Небольшая студия',
        'niche': 'мебель',
        'company_size': '10 человек',
        'business_size': 'малый',
        'company_volume': 'до 5 млн',
        'demand_volume': 'один сайт',
        'tasks': 'заявки с сайта',
        'client_role': 'руководитель',
        'deadline': 'в этом месяце',
        'task_type': 'запуск',
        'product_interest': 'сайт',
        'budget': '150000',
        'contact_method': 'телефон',
        'convenient_time': 'будни после 16',
        'comment': '',
    }


class LeadPayloadTests(unittest.TestCase):
    """Анкета принимает полный пакет и отвергает пустой контакт."""

    def test_should_normalize_email_and_keep_budget_as_text(self) -> None:
        prepared = prepare_lead(lead_payload())
        self.assertEqual(prepared['email'], 'ivan@example.com')
        self.assertEqual(prepared['budget'], '150000')
        self.assertEqual(prepared['client_role'], 'руководитель')

    def test_should_reject_lead_without_phone_and_email(self) -> None:
        payload = lead_payload()
        payload['phone'] = ''
        payload['email'] = ''
        with self.assertRaises(AppError) as caught:
            prepare_lead(payload)
        self.assertEqual(caught.exception.status_code, 400)

    def test_should_reject_unknown_role(self) -> None:
        payload = lead_payload()
        payload['client_role'] = 'владелец'
        with self.assertRaises(AppError):
            prepare_lead(payload)


class BehaviorPayloadTests(unittest.TestCase):
    """Метрики держат время, клики и точки курсора."""

    def test_should_accept_behavior_package(self) -> None:
        prepared = prepare_behavior({
            'lead_id': 1,
            'time_on_page_ms': 12000,
            'button_clicks': [{'name': 'submit', 'count': 1}],
            'cursor_hotspots': [{
                'x': 10,
                'y': 20,
                'duration_ms': 300,
                'selector': '#budget',
            }],
            'return_count': 2,
            'user_agent': 'test',
            'language': 'ru',
            'timezone': 'UTC',
            'screen': '1920x1080',
            'referrer': '',
        })
        self.assertEqual(prepared['lead_id'], 1)
        self.assertIn('submit', str(prepared['button_clicks']))

    def test_should_reject_negative_time(self) -> None:
        with self.assertRaises(AppError):
            prepare_behavior({
                'lead_id': 1,
                'time_on_page_ms': -1,
                'return_count': 0,
            })


class AdminPayloadTests(unittest.TestCase):
    """Диапазон бюджета и цены услуги обязаны расти слева направо."""

    def test_should_reject_inverted_budget_range(self) -> None:
        with self.assertRaises(AppError):
            prepare_admin_settings({
                'services': [],
                'budget_min': 500,
                'budget_max': 500,
                'budget_step': 10,
            })

    def test_should_keep_price_range_per_service(self) -> None:
        prepared = prepare_admin_settings({
            'services': [{
                'code': 'polirovka',
                'title': 'Полировка',
                'description': '',
                'price_min': 5000,
                'price_max': 25000,
                'is_active': True,
            }],
            'budget_min': 5000,
            'budget_max': 120000,
            'budget_step': 1000,
        })
        services = prepared['services']
        self.assertIn('"price_min":5000', services)
        self.assertIn('"price_max":25000', services)

    def test_should_reject_inverted_service_price(self) -> None:
        with self.assertRaises(AppError):
            prepare_admin_settings({
                'services': [{
                    'code': 'polirovka',
                    'title': 'Полировка',
                    'price_min': 100,
                    'price_max': 100,
                    'is_active': True,
                }],
                'budget_min': 0,
                'budget_max': 1000,
                'budget_step': 100,
            })


class SqlSplitTests(unittest.TestCase):
    """Точка с запятой внутри строки не режет команду."""

    def test_should_keep_semicolon_inside_quotes(self) -> None:
        parts = split_sql("COMMENT ON TABLE leads IS 'раз; два'; SELECT 1")
        self.assertEqual(len(parts), 2)
        self.assertIn('раз; два', parts[0])


def collect_paths(router: object, prefix: str = '') -> set[str]:
    """Собирает пути, включая роутеры, которые FastAPI держит вложенными."""
    found: set[str] = set()
    for route in getattr(router, 'routes', []):
        if type(route).__name__ == '_IncludedRouter':
            context = route.include_context
            child_prefix = prefix + (context.prefix or '')
            found.update(collect_paths(context.included_router, child_prefix))
            continue
        found.add(prefix + getattr(route, 'path', ''))
    return found


class RouteTests(unittest.TestCase):
    """Общий роутер публикует все три модели под /api/v1."""

    def test_should_mount_model_routes(self) -> None:
        from app.main import app

        paths = collect_paths(app.router)
        self.assertIn('/api/v1/leads', paths)
        self.assertIn('/api/v1/behavior/{lead_id}', paths)
        self.assertIn('/api/v1/admin-settings', paths)
        self.assertIn('/api/v1/health', paths)


class SchemaDocTests(unittest.TestCase):
    """В докстринге каждой модели лежит SQL её таблицы."""

    def test_should_extract_create_table_for_each_model(self) -> None:
        for model in MODEL_CLASSES:
            sql = extract_table_sql(model)
            self.assertIn('CREATE TABLE', sql)
            self.assertIn(model.table_name, sql)
            for column in model.columns:
                self.assertIn(column, sql)


if __name__ == '__main__':
    unittest.main()
