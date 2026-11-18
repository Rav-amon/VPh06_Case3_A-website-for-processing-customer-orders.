import { useCallback, useEffect, useState } from 'react';
import { fetchCurrentAdmin, loginAdmin, registerAdmin } from '@/api/auth';
import { ApiClientError } from '@/api/client';
import type { IAdminUser } from '@/types/api';
import {
  clearAuthToken,
  readAuthToken,
  writeAuthToken,
} from '@/utils/auth-storage';

interface IAuthState {
  admin: IAdminUser | null;
  loading: boolean;
  error: string | null;
}

/**
 * Хранит сессию администратора и операции входа/выхода.
 */
export function useAuth() {
  const [state, setState] = useState<IAuthState>({
    admin: null,
    loading: true,
    error: null,
  });

  const refresh = useCallback(async () => {
    const token = readAuthToken();
    if (!token) {
      setState({ admin: null, loading: false, error: null });
      return;
    }
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const admin = await fetchCurrentAdmin();
      setState({ admin, loading: false, error: null });
    } catch (error) {
      clearAuthToken();
      const message =
        error instanceof ApiClientError
          ? error.message
          : 'Сессия администратора недействительна';
      setState({ admin: null, loading: false, error: message });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(async (loginValue: string, password: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await loginAdmin(loginValue, password);
      writeAuthToken(result.access_token);
      setState({ admin: result.admin, loading: false, error: null });
      return result.admin;
    } catch (error) {
      const message =
        error instanceof ApiClientError ? error.message : 'Не удалось войти';
      setState({ admin: null, loading: false, error: message });
      throw error;
    }
  }, []);

  const register = useCallback(async (loginValue: string, password: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const result = await registerAdmin(loginValue, password);
      writeAuthToken(result.access_token);
      setState({ admin: result.admin, loading: false, error: null });
      return result.admin;
    } catch (error) {
      const message =
        error instanceof ApiClientError
          ? error.message
          : 'Не удалось зарегистрироваться';
      setState({ admin: null, loading: false, error: message });
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    clearAuthToken();
    setState({ admin: null, loading: false, error: null });
  }, []);

  return {
    admin: state.admin,
    loading: state.loading,
    error: state.error,
    isAuthenticated: state.admin !== null,
    login,
    register,
    logout,
    refresh,
  };
}
