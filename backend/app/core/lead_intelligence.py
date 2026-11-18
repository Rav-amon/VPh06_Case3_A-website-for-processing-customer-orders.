"""Чистый скоринг «температуры» заявки. Одинаковый вход — одинаковый результат."""

from __future__ import annotations

import re
from typing import Literal

TTemperature = Literal['hot', 'warm', 'cold']

HOT_THRESHOLD = 70
WARM_THRESHOLD = 40
MAX_SCORE = 100

_BUDGET_DIGITS = re.compile(r'\d+')

_URGENT_DEADLINE = (
    'сразу',
    'asap',
    'сегодня',
    'завтра',
    'срочно',
    'на этой неделе',
    'в этом месяце',
    'как можно скорее',
    '2 недели',
    'две недели',
)
_SOFT_DEADLINE = (
    'не срочно',
    'когда получится',
    'без срока',
    'потом',
    'квартал',
    'полгода',
    'год',
)
_HOT_NICHES = (
    'финанс',
    'банк',
    'недвиж',
    'девелоп',
    'it',
    'saas',
    'медицин',
    'фарм',
    'b2b',
    'промышл',
)
_COLD_NICHES = (
    'хобби',
    'блог',
    'личн',
    'стартап идея',
    'не определ',
)
_LARGE_SIZE = (
    'крупн',
    '100+',
    '200',
    '500',
    '1000',
    'холдинг',
    'корпорац',
    'enterprise',
)
_SMALL_SIZE = (
    '1-5',
    'до 5',
    'самозанят',
    'фриланс',
    'микро',
    'один человек',
)
_HIGH_VOLUME = (
    'масштаб',
    'сеть',
    'филиал',
    'регион',
    'миллион',
    'комплекс',
    'несколько продукт',
)
_LOW_VOLUME = (
    'маленьк',
    'разово',
    'тест',
    'пилот',
    'одна страница',
    'лендинг',
)
_URGENT_TASK = (
    'запуск',
    'релиз',
    'срочн',
    'переезд',
    'кризис',
    'тендер',
)
_SOFT_TASK = (
    'консультац',
    'идея',
    'посмотреть',
    'просто узнать',
    'интерес',
)


def parse_budget(value: object) -> int:
    """Достаёт целое число бюджета из строки ползунка."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    if not isinstance(value, str):
        return 0
    digits = _BUDGET_DIGITS.findall(value.replace(' ', ''))
    if not digits:
        return 0
    try:
        return int(''.join(digits))
    except ValueError:
        return 0


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(needle in lowered for needle in needles)


def score_lead(lead: dict[str, object]) -> dict[str, object]:
    """Считает температуру, отдел и рекомендацию по полям анкеты."""
    score = 0
    reasons: list[str] = []

    role = str(lead.get('client_role', ''))
    deadline = str(lead.get('deadline', ''))
    niche = str(lead.get('niche', ''))
    company_size = str(lead.get('company_size', ''))
    business_size = str(lead.get('business_size', ''))
    company_volume = str(lead.get('company_volume', ''))
    demand_volume = str(lead.get('demand_volume', ''))
    task_type = str(lead.get('task_type', ''))
    product = str(lead.get('product_interest', ''))
    budget = parse_budget(lead.get('budget', '0'))
    size_blob = f'{company_size} {business_size}'
    volume_blob = f'{company_volume} {demand_volume}'

    if role == 'руководитель':
        score += 18
        reasons.append('Заявку заполняет руководитель')
    else:
        score += 4
        reasons.append('Заявку заполняет сотрудник')

    if _contains_any(deadline, _URGENT_DEADLINE):
        score += 22
        reasons.append('Короткий или срочный срок')
    elif _contains_any(deadline, _SOFT_DEADLINE):
        score += 2
        reasons.append('Срок мягкий, без давления')
    else:
        score += 10
        reasons.append('Срок обычный')

    if budget >= 400_000:
        score += 24
        reasons.append('Высокий бюджет')
    elif budget >= 150_000:
        score += 16
        reasons.append('Средний+ бюджет')
    elif budget >= 50_000:
        score += 8
        reasons.append('Рабочий бюджет')
    else:
        score += 2
        reasons.append('Низкий бюджет')

    if _contains_any(size_blob, _LARGE_SIZE):
        score += 14
        reasons.append('Крупный масштаб компании')
    elif _contains_any(size_blob, _SMALL_SIZE):
        score += 3
        reasons.append('Небольшой масштаб компании')
    else:
        score += 8
        reasons.append('Средний масштаб компании')

    if _contains_any(volume_blob, _HIGH_VOLUME):
        score += 12
        reasons.append('Большой объём задачи или спроса')
    elif _contains_any(volume_blob, _LOW_VOLUME):
        score += 3
        reasons.append('Небольшой объём задачи')
    else:
        score += 7
        reasons.append('Обычный объём задачи')

    if _contains_any(niche, _HOT_NICHES):
        score += 10
        reasons.append('Горячая ниша')
    elif _contains_any(niche, _COLD_NICHES):
        score += 1
        reasons.append('Холодная или неопределённая ниша')
    else:
        score += 5
        reasons.append('Обычная ниша')

    if _contains_any(task_type, _URGENT_TASK):
        score += 10
        reasons.append('Тип задачи требует быстрого запуска')
    elif _contains_any(task_type, _SOFT_TASK):
        score += 2
        reasons.append('Задача скорее исследовательская')
    else:
        score += 5
        reasons.append('Тип задачи стандартный')

    score = max(0, min(MAX_SCORE, score))
    if score >= HOT_THRESHOLD:
        temperature: TTemperature = 'hot'
        temperature_label = 'Горячий'
    elif score >= WARM_THRESHOLD:
        temperature = 'warm'
        temperature_label = 'Тёплый'
    else:
        temperature = 'cold'
        temperature_label = 'Холодный'

    needs_personal_manager = (
        temperature == 'hot'
        or (temperature == 'warm' and role == 'руководитель' and budget >= 150_000)
    )
    worth_time = temperature != 'cold' or budget >= 100_000

    if temperature == 'hot' and (
        _contains_any(size_blob, _LARGE_SIZE) or budget >= 400_000
    ):
        department = 'Enterprise'
        department_hint = 'Крупный или дорогой лид — закрепить за senior-менеджером'
    elif _contains_any(product, ('маркетинг', 'реклам', 'трафик', 'seo', 'smm')):
        department = 'Маркетинг'
        department_hint = 'Запрос ближе к продвижению и трафику'
    elif _contains_any(task_type, ('поддерж', 'сопровожд', 'сервис')):
        department = 'Поддержка'
        department_hint = 'Похоже на сопровождение текущего контура'
    elif temperature == 'cold':
        department = 'Квалификация'
        department_hint = 'Сначала коротко квалифицировать, не тратить senior-время'
    else:
        department = 'Продажи'
        department_hint = 'Стандартный коммерческий разбор и КП'

    if temperature == 'hot':
        priority_advice = 'Брать в работу сразу: высокий шанс сделки'
    elif temperature == 'warm':
        priority_advice = 'Стоит связаться сегодня, но без аврала'
    else:
        priority_advice = 'Можно поставить в хвост очереди или отправить автоответ'

    return {
        'score': score,
        'temperature': temperature,
        'temperature_label': temperature_label,
        'worth_time': worth_time,
        'needs_personal_manager': needs_personal_manager,
        'recommended_department': department,
        'department_hint': department_hint,
        'priority_advice': priority_advice,
        'reasons': reasons,
        'budget_value': budget,
    }


def enrich_lead(lead: dict[str, object]) -> dict[str, object]:
    """Добавляет блок intelligence к строке заявки."""
    return {
        **lead,
        'intelligence': score_lead(lead),
    }


def sort_leads_by_temperature(
    leads: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Сортирует: горячие сверху, внутри группы — выше score и новее."""
    enriched = [enrich_lead(item) for item in leads]

    def sort_key(item: dict[str, object]) -> tuple[int, int, str]:
        intelligence = item.get('intelligence', {})
        if not isinstance(intelligence, dict):
            return (9, 0, '')
        temperature = str(intelligence.get('temperature', 'cold'))
        rank = {'hot': 0, 'warm': 1, 'cold': 2}.get(temperature, 3)
        score = int(intelligence.get('score', 0) or 0)
        created = str(item.get('created_at', ''))
        return (rank, -score, created)

    return sorted(enriched, key=sort_key)


def summarize_intelligence(
    leads: list[dict[str, object]],
) -> dict[str, object]:
    """Сводка по температурам для шапки очереди заявок."""
    hot = 0
    warm = 0
    cold = 0
    personal = 0
    worth = 0
    score_sum = 0
    for item in leads:
        intelligence = item.get('intelligence')
        if not isinstance(intelligence, dict):
            continue
        temperature = intelligence.get('temperature')
        if temperature == 'hot':
            hot += 1
        elif temperature == 'warm':
            warm += 1
        else:
            cold += 1
        if intelligence.get('needs_personal_manager'):
            personal += 1
        if intelligence.get('worth_time'):
            worth += 1
        score_sum += int(intelligence.get('score', 0) or 0)
    total = len(leads)
    return {
        'total': total,
        'hot': hot,
        'warm': warm,
        'cold': cold,
        'needs_personal_manager': personal,
        'worth_time': worth,
        'average_score': round(score_sum / total, 1) if total else 0,
    }
