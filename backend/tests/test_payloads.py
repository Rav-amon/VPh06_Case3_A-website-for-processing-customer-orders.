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
from app.core.lead_intelligence import score_lead, sort_leads_by_temperature
from app.models.admin import prepare_admin_credentials
from app.models.admin_settings import prepare_admin_settings
from app.models.behavior import prepare_behavior
from app.models.behavior_metrics import prepare_behavior_metrics
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


class LeadIntelligenceTests(unittest.TestCase):
    """Горячие лиды получают высокий score и поднимаются в очереди."""

    def test_should_mark_urgent_lead_as_hot(self) -> None:
        result = score_lead({
            'client_role': 'руководитель',
            'deadline': 'сегодня',
            'niche': 'финансы B2B',
            'company_size': '500 человек',
            'business_size': 'крупный холдинг',
            'company_volume': 'сеть филиалов',
            'demand_volume': 'комплексный запуск',
            'task_type': 'срочный запуск',
            'product_interest': 'сайт',
            'budget': '450000',
        })
        self.assertEqual(result['temperature'], 'hot')
        self.assertTrue(result['needs_personal_manager'])
        self.assertGreaterEqual(int(result['score']), 70)

    def test_should_sort_hot_before_cold(self) -> None:
        ranked = sort_leads_by_temperature([
            {
                'id': 1,
                'client_role': 'сотрудник',
                'deadline': 'когда получится',
                'niche': 'хобби блог',
                'company_size': '1-5',
                'business_size': 'микро',
                'company_volume': 'разово',
                'demand_volume': 'лендинг',
                'task_type': 'просто узнать',
                'product_interest': 'консультация',
                'budget': '15000',
                'created_at': '2026-01-01T00:00:00Z',
            },
            {
                'id': 2,
                'client_role': 'руководитель',
                'deadline': 'срочно',
                'niche': 'недвижимость',
                'company_size': '200+',
                'business_size': 'корпорация',
                'company_volume': 'региональная сеть',
                'demand_volume': 'несколько продуктов',
                'task_type': 'запуск',
                'product_interest': 'платформа',
                'budget': '500000',
                'created_at': '2026-01-02T00:00:00Z',
            },
        ])
        self.assertEqual(ranked[0]['id'], 2)
        self.assertEqual(ranked[0]['intelligence']['temperature'], 'hot')


class LiveMetricsPayloadTests(unittest.TestCase):
    """Живые метрики принимают секунды и строковые JSON-поля."""

    def test_should_accept_live_metrics_package(self) -> None:
        prepared = prepare_behavior_metrics({
            'application_id': 0,
            'time_on_page': 12,
            'buttons_clicked': '{"submit":1}',
            'cursor_positions': '[{"x":10,"y":20,"t":12}]',
            'return_frequency': 0,
        })
        self.assertEqual(prepared['time_on_page'], 12)
        self.assertIn('submit', prepared['buttons_clicked'])

    def test_should_reject_negative_seconds(self) -> None:
        with self.assertRaises(AppError):
            prepare_behavior_metrics({
                'application_id': 0,
                'time_on_page': -1,
                'buttons_clicked': '',
                'cursor_positions': '',
                'return_frequency': 0,
            })


class AdminUserPayloadTests(unittest.TestCase):
    """Логин и пароль администратора проходят базовую проверку."""

    def test_should_normalize_login_and_hash_password(self) -> None:
        prepared = prepare_admin_credentials({
            'login': 'Ravil.Admin',
            'password': 'SecretPass1',
        })
        self.assertEqual(prepared['login'], 'ravil.admin')
        self.assertNotEqual(prepared['password_hash'], 'SecretPass1')
        self.assertTrue(prepared['password_hash'].startswith('$2'))

    def test_should_reject_short_password(self) -> None:
        with self.assertRaises(AppError):
            prepare_admin_credentials({
                'login': 'admin',
                'password': 'short',
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
        self.assertIn('/api/v1/auth/login', paths)
        self.assertIn('/api/v1/auth/register', paths)
        self.assertIn('/api/v1/auth/bootstrap-status', paths)
        self.assertIn('/api/v1/stats', paths)
        self.assertIn('/api/v1/health', paths)
        self.assertIn('/api/behavior-metrics/', paths)
        self.assertIn('/api/behavior-metrics', paths)
        self.assertIn('/api/applications/', paths)
        self.assertIn('/api/applications', paths)


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
