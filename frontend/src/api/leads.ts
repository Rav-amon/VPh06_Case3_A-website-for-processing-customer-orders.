import { apiRequest } from '@/api/client';
import type {
  IAdminSettings,
  IBehaviorPayload,
  ILeadCreated,
  ILeadPayload,
} from '@/types/api';

/** Читает услуги и диапазон бюджета для формы. */
export function fetchAdminSettings(): Promise<IAdminSettings> {
  return apiRequest<IAdminSettings>('/api/v1/admin-settings');
}

/** Отправляет анкету тёплого клиента. */
export function createLead(payload: ILeadPayload): Promise<ILeadCreated> {
  return apiRequest<ILeadCreated>('/api/v1/leads', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/** Отправляет пакет метрик поведения для заявки. */
export function createBehavior(payload: IBehaviorPayload): Promise<unknown> {
  return apiRequest('/api/v1/behavior', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
