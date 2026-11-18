import { apiRequest } from '@/api/client';
import type { IAuthTokenResponse, IAdminUser, IBootstrapStatus } from '@/types/api';

/** Сообщает, открыта ли регистрация первого администратора. */
export function fetchBootstrapStatus(): Promise<IBootstrapStatus> {
  return apiRequest<IBootstrapStatus>('/api/v1/auth/bootstrap-status');
}

/** Регистрирует первого администратора и возвращает JWT. */
export function registerAdmin(
  login: string,
  password: string,
): Promise<IAuthTokenResponse> {
  return apiRequest<IAuthTokenResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ login, password }),
  });
}

/** Выполняет вход администратора и возвращает JWT. */
export function loginAdmin(
  login: string,
  password: string,
): Promise<IAuthTokenResponse> {
  return apiRequest<IAuthTokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ login, password }),
  });
}

/** Проверяет действующий JWT и возвращает профиль. */
export function fetchCurrentAdmin(): Promise<IAdminUser> {
  return apiRequest<IAdminUser>('/api/v1/auth/me', { auth: true });
}
