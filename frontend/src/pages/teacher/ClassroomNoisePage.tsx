import { useState } from 'react';
import type { NoiseSessionDto } from '@/api/types';
import { api } from '@/api/client';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { useFetch } from '@/hooks/useFetch';

export function ClassroomNoisePage() {
  const { data: classesData } = useFetch(() => api.classes.list(), []);
  const { data: subjectsData } = useFetch(() => api.subjects.list(), []);

  const [classId, setClassId] = useState('');
  const [subjectId, setSubjectId] = useState('');
  const [session, setSession] = useState<NoiseSessionDto | null>(null);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const classes = classesData?.items ?? [];
  const subjects = subjectsData?.items ?? [];

  const start = async () => {
    if (!classId || !subjectId) {
      setError('Выберите класс и предмет');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const s = await api.noise.startSession(classId, subjectId);
      setSession(s);
      setRecording(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось начать сессию');
    } finally {
      setLoading(false);
    }
  };

  const stop = async () => {
    if (!session) return;
    setLoading(true);
    setError(null);
    try {
      const report = await api.noise.stopSession(session.id);
      setSession(report);
      setRecording(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось завершить сессию');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <PageHeader
        title="Анализ шума в классе"
        description="Запись урока, визуализация шума, отчёт в конце занятия"
        actions={
          <button
            type="button"
            className={`btn ${recording ? 'btn--danger' : 'btn--primary'}`}
            disabled={loading || (!recording && (!classId || !subjectId))}
            onClick={() => void (recording ? stop() : start())}
          >
            {loading ? '…' : recording ? 'Остановить анализ' : 'Начать анализ урока'}
          </button>
        }
      />
      {error && <div className="auth-alert">{error}</div>}
      {!recording && !session && (
        <PlaceholderCard title="Параметры урока">
          <div className="inline-form">
            <label>
              Класс
              <select className="input" value={classId} onChange={(e) => setClassId(e.target.value)}>
                <option value="">Выберите класс</option>
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Предмет
              <select
                className="input"
                value={subjectId}
                onChange={(e) => setSubjectId(e.target.value)}
              >
                <option value="">Выберите предмет</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </PlaceholderCard>
      )}
      <div className="form-grid">
        <PlaceholderCard title="Уровень шума">
          <div
            className={`recording-indicator${recording ? ' recording-indicator--active' : ''}`}
          >
            {recording ? 'Идёт запись…' : session ? 'Сессия завершена' : 'Запись не активна'}
          </div>
          {session && session.samples.length > 0 ? (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Время замера</th>
                    <th>Уровень шума, дБ</th>
                  </tr>
                </thead>
                <tbody>
                  {session.samples.map((s, i) => (
                    <tr key={i}>
                      <td>{new Date(s.timestamp).toLocaleTimeString()}</td>
                      <td>{s.level_db.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="chart-placeholder" aria-hidden />
          )}
        </PlaceholderCard>
        <PlaceholderCard title="Самые громкие ученики">
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                <th>Ученик</th>
                <th>Средний уровень, дБ</th>
                <th>Пиковый уровень, дБ</th>
                <th>Нарушений, раз</th>
                </tr>
              </thead>
              <tbody>
                {session?.top_noisy_students.length ? (
                  session.top_noisy_students.map((st) => (
                    <tr key={st.student_id}>
                      <td>{st.student_name}</td>
                      <td>{st.avg_level_db.toFixed(1)}</td>
                      <td>{st.peak_level_db.toFixed(1)}</td>
                      <td>{st.incidents_count}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="muted">
                      Данные появятся после завершения анализа
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </PlaceholderCard>
        <PlaceholderCard title="Выжимка урока">
          <p className="muted">
            {session?.summary ??
              'По завершении урока ИИ сформирует краткий отчёт для вас и отмеченных учеников.'}
          </p>
        </PlaceholderCard>
      </div>
    </div>
  );
}
