import { FormEvent, useEffect, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { fetchBootstrapStatus } from '@/api/auth';
import { ApiClientError } from '@/api/client';
import { Field } from '@/components/Field';
import { GoldOrbs } from '@/components/GoldOrbs';
import { useAuth } from '@/hooks/use-auth';

const MIN_PASSWORD_LENGTH = 8;

function submitLabel(
  submitting: boolean,
  mode: 'login' | 'register',
): string {
  if (submitting) {
    return 'Подождите…';
  }
  if (mode === 'register') {
    return 'Зарегистрироваться';
  }
  return 'Войти';
}

/** Страница входа. Кнопка регистрации видна только пока админов нет. */
export function AdminLoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, loading, login, register } = useAuth();
  const [loginValue, setLoginValue] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [registrationOpen, setRegistrationOpen] = useState(false);
  const [statusLoading, setStatusLoading] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [touched, setTouched] = useState({ login: false, password: false });

  useEffect(() => {
    let active = true;
    const loadStatus = async () => {
      try {
        const status = await fetchBootstrapStatus();
        if (!active) {
          return;
        }
        setRegistrationOpen(status.registration_open);
        if (status.registration_open) {
          setMode('register');
        }
      } catch (error) {
        if (!active) {
          return;
        }
        const message =
          error instanceof ApiClientError
            ? error.message
            : 'Не удалось проверить статус регистрации';
        setFormError(message);
      } finally {
        if (active) {
          setStatusLoading(false);
        }
      }
    };
    void loadStatus();
    return () => {
      active = false;
    };
  }, []);

  if (!loading && isAuthenticated) {
    return <Navigate to="/admin" replace />;
  }

  const loginError =
    touched.login && loginValue.trim().length < 3
      ? 'Логин не короче 3 символов'
      : undefined;
  const passwordError =
    touched.password && password.length < MIN_PASSWORD_LENGTH
      ? `Пароль не короче ${MIN_PASSWORD_LENGTH} символов`
      : undefined;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setTouched({ login: true, password: true });
    if (loginValue.trim().length < 3 || password.length < MIN_PASSWORD_LENGTH) {
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      if (mode === 'register') {
        await register(loginValue.trim(), password);
      } else {
        await login(loginValue.trim(), password);
      }
      navigate('/admin', { replace: true });
    } catch (error) {
      const message =
        error instanceof ApiClientError
          ? error.message
          : 'Не удалось выполнить запрос';
      setFormError(message);
      if (mode === 'register' && error instanceof ApiClientError) {
        if (error.status === 403 || error.code === 'forbidden') {
          setRegistrationOpen(false);
          setMode('login');
        }
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden px-5 pb-24 pt-10 sm:px-8">
      <GoldOrbs />
      <div className="relative z-10 mx-auto max-w-md animate-rise">
        <p className="font-display text-4xl text-gold-100 sm:text-5xl">
          Autéllo
        </p>
        <h1 className="mt-4 font-display text-2xl italic text-gold-200/85">
          Панель администратора
        </h1>
        <p className="mt-3 text-sm text-mist/65">
          {mode === 'register'
            ? 'Создайте первого администратора. После этого регистрация закроется.'
            : 'Войдите по логину и паролю, чтобы управлять услугами и статистикой.'}
        </p>

        <form
          className="mt-10 space-y-6"
          onSubmit={(event) => {
            void handleSubmit(event);
          }}
          noValidate
        >
          <Field
            id="admin-login"
            label="Логин"
            value={loginValue}
            required
            error={loginError}
            onChange={setLoginValue}
            onBlur={() => setTouched((prev) => ({ ...prev, login: true }))}
          />
          <Field
            id="admin-password"
            label="Пароль"
            type="password"
            value={password}
            required
            error={passwordError}
            onChange={setPassword}
            onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
          />

          {formError ? (
            <p className="field-error" role="alert">
              {formError}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={submitting || statusLoading}
            className="w-full border border-gold-400/40 bg-gold-400/10 px-5 py-3
              text-sm uppercase tracking-[0.18em] text-gold-100 transition
              hover:bg-gold-400/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitLabel(submitting, mode)}
          </button>
        </form>

        {!statusLoading && registrationOpen && mode === 'login' ? (
          <button
            type="button"
            className="mt-6 text-sm text-gold-300 underline-offset-4 hover:underline"
            onClick={() => {
              setMode('register');
              setFormError(null);
            }}
          >
            Зарегистрироваться
          </button>
        ) : null}

        {!statusLoading && registrationOpen && mode === 'register' ? (
          <button
            type="button"
            className="mt-6 text-sm text-gold-300 underline-offset-4 hover:underline"
            onClick={() => {
              setMode('login');
              setFormError(null);
            }}
          >
            Уже есть аккаунт? Войти
          </button>
        ) : null}

        <Link
          to="/"
          className="mt-10 inline-block text-sm text-mist/55 hover:text-gold-200"
        >
          На главную
        </Link>
      </div>
    </main>
  );
}
