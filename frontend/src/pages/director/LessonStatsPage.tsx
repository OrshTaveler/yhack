import { useState } from 'react';
import type { NoiseSessionDto } from '@/api/types';
import { api } from '@/api/client';
import { AsyncState } from '@/components/common/AsyncState';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { useFetch } from '@/hooks/useFetch';

const STATUS_LABEL: Record<string, string> = {
  recording: 'Запись',
  processing: 'Обработка',
  ready: 'Готово',
};

export function LessonStatsPage() {
  const { data, loading, error } = useFetch(() => api.noise.listLessonStats(), []);
  const [selected, setSelected] = useState<NoiseSessionDto | null>(null);
  const items = data?.items ?? [];

  return (
    <div className="page">
      <PageHeader
        title="Статистика уроков"
        description="Уровень шума в классе и краткая выжимка по завершённым урокам"
      />
      <div className="form-grid">
        <PlaceholderCard title="Список уроков">
          <AsyncState loading={loading} error={error} empty={items.length === 0}>
            <ul className="list">
              {items.map((lesson) => (
                <li
                  key={lesson.id}
                  className={`list__item list__item--clickable${selected?.id === lesson.id ? ' list__item--active' : ''}`}
                  onClick={() => setSelected(lesson)}
                >
                  <span>
                    {lesson.class_name} · {lesson.subject_name} ·{' '}
                    {new Date(lesson.started_at).toLocaleString()}
                  </span>
                  <span className="badge">{STATUS_LABEL[lesson.status] ?? lesson.status}</span>
                </li>
              ))}
            </ul>
          </AsyncState>
        </PlaceholderCard>
        <PlaceholderCard title="Детали урока">
          {!selected ? (
            <p className="muted">Выберите урок из списка</p>
          ) : (
            <>
              {selected.samples.length > 0 ? (
                <div className="table-scroll">
                  <p className="muted" style={{ marginBottom: '0.5rem' }}>
                    Измерения шума по времени
                  </p>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Время</th>
                        <th>Уровень, дБ</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selected.samples.map((s, i) => (
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
              <h3 style={{ marginTop: '1rem' }}>Выжимка</h3>
              <p className="muted">{selected.summary ?? 'Отчёт ещё не готов'}</p>
              {selected.top_noisy_students.length > 0 && (
                <>
                  <h3 style={{ marginTop: '1rem' }}>Самые активные ученики</h3>
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
                        {selected.top_noisy_students.map((st) => (
                          <tr key={st.student_id}>
                            <td>{st.student_name}</td>
                            <td>{st.avg_level_db.toFixed(1)}</td>
                            <td>{st.peak_level_db.toFixed(1)}</td>
                            <td>{st.incidents_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </>
          )}
        </PlaceholderCard>
      </div>
    </div>
  );
}
