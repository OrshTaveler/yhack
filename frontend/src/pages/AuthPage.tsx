import { type FormEvent, useEffect, useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { MOCK_ACCOUNTS, ROLE_LABELS } from '@/data/mockAccounts';
import { homePathForRole } from '@/config/navigation';
import { useAuth } from '@/hooks/useAuth';
import type { UserRole } from '@/types';

type AuthTab = 'login' | 'register';

export function AuthPage() {
  const { user, login, register } = useAuth();
  const location = useLocation();
  const initialTab: AuthTab = location.pathname === '/register' ? 'register' : 'login';
  const [tab, setTab] = useState<AuthTab>(initialTab);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setTab(location.pathname === '/register' ? 'register' : 'login');
    setError(null);
  }, [location.pathname]);

  if (user) {
    return <Navigate to={homePathForRole(user.role)} replace />;
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-card__header">
          <span className="auth-card__logo">ПУ</span>
          <div>
            <h1>Помощник учителя</h1>
            <p className="auth-card__subtitle">
              {tab === 'login' ? 'Вход в личный кабинет' : 'Регистрация'}
            </p>
          </div>
        </div>

        <div className="auth-tabs" role="tablist">
          <Link
            to="/login"
            role="tab"
            aria-selected={tab === 'login'}
            className={`auth-tabs__btn${tab === 'login' ? ' auth-tabs__btn--active' : ''}`}
            onClick={() => {
              setTab('login');
              setError(null);
            }}
          >
            Вход
          </Link>
          <Link
            to="/register"
            role="tab"
            aria-selected={tab === 'register'}
            className={`auth-tabs__btn${tab === 'register' ? ' auth-tabs__btn--active' : ''}`}
            onClick={() => {
              setTab('register');
              setError(null);
            }}
          >
            Регистрация
          </Link>
        </div>

        {error && (
          <div className="auth-alert" role="alert">
            {error}
          </div>
        )}

        {tab === 'login' ? (
          <LoginForm
            loading={loading}
            onSubmit={async (email, password) => {
              setLoading(true);
              setError(null);
              try {
                await login(email, password);
              } catch (e) {
                setError(e instanceof Error ? e.message : 'Ошибка входа');
              } finally {
                setLoading(false);
              }
            }}
          />
        ) : (
          <RegisterForm
            loading={loading}
            onError={setError}
            onSubmit={async (data) => {
              setLoading(true);
              setError(null);
              try {
                await register(data);
              } catch (e) {
                setError(e instanceof Error ? e.message : 'Ошибка регистрации');
              } finally {
                setLoading(false);
              }
            }}
          />
        )}

        <details className="auth-demo">
          <summary>Демо-аккаунты для входа</summary>
          <ul className="auth-demo__list">
            {MOCK_ACCOUNTS.map((a) => (
              <li key={a.email}>
                <code>{a.email}</code> / <code>{a.password}</code>
                <span className="muted"> — {ROLE_LABELS[a.user.role]}</span>
              </li>
            ))}
          </ul>
        </details>
      </div>
    </div>
  );
}

function LoginForm({
  loading,
  onSubmit,
}: {
  loading: boolean;
  onSubmit: (email: string, password: string) => Promise<void>;
}) {
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    void onSubmit(String(fd.get('email')), String(fd.get('password')));
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Email</span>
        <input
          className="input"
          type="email"
          name="email"
          required
          autoComplete="email"
          placeholder="teacher@school.ru"
        />
      </label>
      <label className="field">
        <span>Пароль</span>
        <input
          className="input"
          type="password"
          name="password"
          required
          autoComplete="current-password"
          placeholder="••••••••"
        />
      </label>
      <button type="submit" className="btn btn--primary btn--block" disabled={loading}>
        {loading ? 'Вход…' : 'Войти'}
      </button>
    </form>
  );
}

function RegisterForm({
  loading,
  onError,
  onSubmit,
}: {
  loading: boolean;
  onError: (msg: string | null) => void;
  onSubmit: (data: {
    name: string;
    email: string;
    password: string;
    role: UserRole;
  }) => Promise<void>;
}) {
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const password = String(fd.get('password'));
    const confirm = String(fd.get('confirmPassword'));
    if (password !== confirm) {
      onError('Пароли не совпадают');
      return;
    }
    onError(null);
    void onSubmit({
      name: String(fd.get('name')),
      email: String(fd.get('email')),
      password,
      role: String(fd.get('role')) as UserRole,
    });
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>ФИО</span>
        <input className="input" type="text" name="name" required placeholder="Иванов И.И." />
      </label>
      <label className="field">
        <span>Email</span>
        <input
          className="input"
          type="email"
          name="email"
          required
          autoComplete="email"
          placeholder="user@school.ru"
        />
      </label>
      <label className="field">
        <span>Роль</span>
        <select className="input" name="role" required defaultValue="student">
          <option value="student">Ученик</option>
          <option value="teacher">Учитель</option>
          <option value="director">Директор</option>
        </select>
      </label>
      <label className="field">
        <span>Пароль</span>
        <input
          className="input"
          type="password"
          name="password"
          required
          minLength={6}
          autoComplete="new-password"
        />
      </label>
      <label className="field">
        <span>Повторите пароль</span>
        <input
          className="input"
          type="password"
          name="confirmPassword"
          required
          minLength={6}
          autoComplete="new-password"
        />
      </label>
      <button type="submit" className="btn btn--primary btn--block" disabled={loading}>
        {loading ? 'Регистрация…' : 'Зарегистрироваться'}
      </button>
    </form>
  );
}
