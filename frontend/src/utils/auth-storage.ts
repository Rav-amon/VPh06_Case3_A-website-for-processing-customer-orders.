const TOKEN_KEY = 'autello_admin_token';

/** Читает JWT администратора из localStorage. */
export function readAuthToken(): string | null {
  const value = window.localStorage.getItem(TOKEN_KEY);
  if (value === null || value.trim() === '') {
    return null;
  }
  return value;
}

/** Сохраняет JWT администратора. */
export function writeAuthToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

/** Удаляет JWT при выходе. */
export function clearAuthToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}
