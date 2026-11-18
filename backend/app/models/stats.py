"""Агрегаты по заявкам и поведению для панели администратора."""

from __future__ import annotations

from app.core.database import Database

RECENT_LEADS_LIMIT = 20
DAYS_WINDOW = 30


class StatsCrud:
    """Сбор статистики без отдельной таблицы: читает leads и lead_behavior."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def overview(self) -> dict[str, object]:
        """Собирает сводку: объёмы, разрезы и свежие заявки."""
        total_leads = await self._database.fetchval(
            'SELECT COUNT(*)::int FROM leads'
        )
        total_with_behavior = await self._database.fetchval(
            'SELECT COUNT(*)::int FROM lead_behavior'
        )
        avg_time = await self._database.fetchval(
            '''
            SELECT COALESCE(AVG(time_on_page_ms), 0)::bigint
            FROM lead_behavior
            '''
        )
        avg_returns = await self._database.fetchval(
            '''
            SELECT COALESCE(AVG(return_count), 0)::float
            FROM lead_behavior
            '''
        )
        by_role = await self._database.fetch(
            '''
            SELECT client_role AS name, COUNT(*)::int AS count
            FROM leads
            GROUP BY client_role
            ORDER BY count DESC, name
            '''
        )
        by_product = await self._database.fetch(
            '''
            SELECT product_interest AS name, COUNT(*)::int AS count
            FROM leads
            GROUP BY product_interest
            ORDER BY count DESC, name
            LIMIT 20
            '''
        )
        by_day = await self._database.fetch(
            '''
            SELECT
                to_char(created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD') AS day,
                COUNT(*)::int AS count
            FROM leads
            WHERE created_at >= (NOW() AT TIME ZONE 'UTC') - ($1::int * INTERVAL '1 day')
            GROUP BY 1
            ORDER BY 1
            ''',
            DAYS_WINDOW,
        )
        recent = await self._database.fetch(
            '''
            SELECT
                id,
                first_name,
                last_name,
                phone,
                email,
                product_interest,
                budget,
                client_role,
                created_at
            FROM leads
            ORDER BY created_at DESC, id DESC
            LIMIT $1
            ''',
            RECENT_LEADS_LIMIT,
        )
        return {
            'total_leads': int(total_leads or 0),
            'total_with_behavior': int(total_with_behavior or 0),
            'avg_time_on_page_ms': int(avg_time or 0),
            'avg_return_count': float(avg_returns or 0),
            'by_role': by_role,
            'by_product': by_product,
            'by_day': by_day,
            'recent_leads': recent,
            'days_window': DAYS_WINDOW,
        }
