import { apiRequest } from '@/api/client';
import type { IAdminSettings, IAdminStats, IServiceItem } from '@/types/api';

export interface IAdminSettingsPayload {
  services: IServiceItem[];
  budget_min: number;
  budget_max: number;
  budget_step: number;
}

/** Читает услуги и диапазон бюджета. */
export function fetchAdminSettings(): Promise<IAdminSettings> {
  return apiRequest<IAdminSettings>('/api/v1/admin-settings');
}

/** Сохраняет услуги и диапазон бюджета (нужен JWT). */
export function updateAdminSettings(
  payload: IAdminSettingsPayload,
): Promise<IAdminSettings> {
  return apiRequest<IAdminSettings>('/api/v1/admin-settings', {
    method: 'PUT',
    auth: true,
    body: JSON.stringify(payload),
  });
}

/** Загружает сводную статистику заявок (нужен JWT). */
export function fetchAdminStats(): Promise<IAdminStats> {
  return apiRequest<IAdminStats>('/api/v1/stats', { auth: true });
}
