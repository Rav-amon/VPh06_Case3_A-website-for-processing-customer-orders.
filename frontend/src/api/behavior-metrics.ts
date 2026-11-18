import { apiRequest } from '@/api/client';
import type { IBehaviorMetricsPage } from '@/types/behavior-metrics';

export interface IBehaviorMetricsPayload {
  application_id: number;
  time_on_page: number;
  buttons_clicked: string;
  cursor_positions: string;
  return_frequency: number;
}

export interface IBehaviorMetricsCreated {
  id: number;
}

/** Отправляет снимок живых метрик на POST /api/behavior-metrics/. */
export function postBehaviorMetrics(
  payload: IBehaviorMetricsPayload,
): Promise<IBehaviorMetricsCreated> {
  return apiRequest<IBehaviorMetricsCreated>('/api/behavior-metrics/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Читает снимки метрик для админ-хитмапа.
 * Нужен JWT. skip — смещение, как в запросе ?skip=0&limit=100.
 */
export function fetchBehaviorMetrics(
  skip = 0,
  limit = 100,
): Promise<IBehaviorMetricsPage> {
  const params = new URLSearchParams({
    skip: String(skip),
    limit: String(limit),
  });
  return apiRequest<IBehaviorMetricsPage>(
    `/api/behavior-metrics/?${params.toString()}`,
    { auth: true },
  );
}
