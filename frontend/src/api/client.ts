import type { IApiResponse } from '@/types/api';
import { clearAuthToken, readAuthToken } from '@/utils/auth-storage';

const REQUEST_TIMEOUT_MS = 20000;

export class ApiClientError extends Error {
  readonly code: string;
  readonly details: unknown;
  readonly status: number;

  constructor(code: string, message: string, status: number, details: unknown) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

interface IApiRequestOptions extends RequestInit {
  auth?: boolean;
}

/**
 * Выполняет JSON-запрос к публичному API через Nginx.
 */
export async function apiRequest<T>(
  path: string,
  init?: IApiRequestOptions,
): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const { auth = false, headers, ...rest } = init ?? {};

  try {
    const requestHeaders: Record<string, string> = {
      Accept: 'application/json',
      ...(rest.body ? { 'Content-Type': 'application/json' } : {}),
      ...(headers as Record<string, string> | undefined),
    };

    if (auth) {
      const token = readAuthToken();
      if (token) {
        requestHeaders.Authorization = `Bearer ${token}`;
      }
    }

    const response = await fetch(path, {
      ...rest,
      signal: controller.signal,
      headers: requestHeaders,
    });

    let payload: IApiResponse<T>;
    try {
      payload = (await response.json()) as IApiResponse<T>;
    } catch {
      throw new ApiClientError(
        'invalid_response',
        'Сервер вернул неожиданный ответ',
        response.status,
        null,
      );
    }

    if (!response.ok || payload.error) {
      if (auth && response.status === 401) {
        clearAuthToken();
      }
      throw new ApiClientError(
        payload.error?.code ?? 'http_error',
        payload.error?.message ?? payload.message ?? 'Запрос не выполнен',
        response.status,
        payload.error?.details ?? null,
      );
    }

    return payload.data;
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiClientError(
        'timeout',
        'Превышено время ожидания ответа',
        408,
        null,
      );
    }
    throw new ApiClientError(
      'network_error',
      'Не удалось связаться с сервером',
      0,
      null,
    );
  } finally {
    window.clearTimeout(timer);
  }
}
