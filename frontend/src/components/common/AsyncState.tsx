import type { ReactNode } from 'react';

interface AsyncStateProps {
  loading: boolean;
  error: string | null;
  empty?: boolean;
  emptyText?: string;
  children: ReactNode;
}

export function AsyncState({
  loading,
  error,
  empty,
  emptyText = 'Нет данных',
  children,
}: AsyncStateProps) {
  if (loading) {
    return <p className="muted">Загрузка…</p>;
  }
  if (error) {
    return (
      <div className="auth-alert" role="alert">
        {error}
      </div>
    );
  }
  if (empty) {
    return <p className="muted">{emptyText}</p>;
  }
  return <>{children}</>;
}
