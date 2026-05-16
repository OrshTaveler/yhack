import { api } from '@/api/client';
import type { ProgressPointDto, SubjectLevel } from '@/api/types';
import { AsyncState } from '@/components/common/AsyncState';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { StatCard } from '@/components/common/StatCard';
import { useFetch } from '@/hooks/useFetch';

const LEVEL_LABEL: Record<SubjectLevel, string> = {
  weak: 'Нужно подтянуть',
  normal: 'Средний уровень',
  strong: 'Сильная сторона',
};

const STATUS_LABEL: Record<string, string> = {
  pending: 'На проверке ИИ',
  ai_reviewed: 'Проверено ИИ',
  teacher_reviewed: 'Оценено учителем',
};

/** Простой линейный график прогресса без сторонних библиотек. */
function ProgressChart({ points }: { points: ProgressPointDto[] }) {
  if (points.length === 0) {
    return <p className="muted">Пока нет проверенных работ для графика</p>;
  }

  const width = 520;
  const height = 160;
  const padding = 28;
  const maxGrade = 5;
  const minGrade = 2;

  const stepX =
    points.length > 1 ? (width - padding * 2) / (points.length - 1) : 0;
  const scaleY = (grade: number) =>
    height -
    padding -
    ((grade - minGrade) / (maxGrade - minGrade)) * (height - padding * 2);

  const coords = points.map((p, i) => ({
    x: padding + stepX * i,
    y: scaleY(p.grade),
    point: p,
  }));

  const linePath = coords
    .map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x} ${c.y}`)
    .join(' ');

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="progress-chart"
      role="img"
      aria-label="График успеваемости"
    >
      {[2, 3, 4, 5].map((g) => (
        <g key={g}>
          <line
            x1={padding}
            x2={width - padding}
            y1={scaleY(g)}
            y2={scaleY(g)}
            stroke="#e5e7eb"
            strokeWidth={1}
          />
          <text x={4} y={scaleY(g) + 4} fontSize={11} fill="#9ca3af">
            {g}
          </text>
        </g>
      ))}
      <path d={linePath} fill="none" stroke="#4f46e5" strokeWidth={2.5} />
      {coords.map((c, i) => (
        <circle key={i} cx={c.x} cy={c.y} r={4} fill="#4f46e5">
          <title>
            {c.point.subject_name}: {c.point.grade} (
            {new Date(c.point.date).toLocaleDateString()})
          </title>
        </circle>
      ))}
    </svg>
  );
}

export function StudentProfilePage() {
  const { data, loading, error } = useFetch(() => api.profile.me(), []);

  return (
    <div className="page">
      <PageHeader
        title="Мой профиль"
        description="Прогресс, сильные и слабые темы, история работ"
      />
      <AsyncState loading={loading} error={error}>
        {data && (
          <>
            <div className="stats-row">
              <StatCard
                value={data.average_grade || '—'}
                label="Средний балл"
                unit="по шкале 2–5"
              />
              <StatCard value={data.total_works} label="Всего работ" unit="шт." />
              <StatCard
                value={data.checked_works}
                label="Проверено"
                unit="шт."
              />
            </div>

            {(data.best_subject || data.weak_subjects.length > 0) && (
              <div className="form-grid">
                {data.best_subject && (
                  <PlaceholderCard title="Сильная сторона">
                    <p className="profile-highlight profile-highlight--strong">
                      {data.best_subject}
                    </p>
                    <p className="muted">
                      Лучший средний балл среди ваших предметов
                    </p>
                  </PlaceholderCard>
                )}
                {data.weak_subjects.length > 0 && (
                  <PlaceholderCard title="Над чем поработать">
                    <div className="chip-row">
                      {data.weak_subjects.map((s) => (
                        <span
                          key={s}
                          className="chip chip--weak"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                    <p className="muted">
                      Эти темы стоит повторить — попросите AI-помощника объяснить
                    </p>
                  </PlaceholderCard>
                )}
              </div>
            )}

            <PlaceholderCard title="Динамика успеваемости">
              <ProgressChart points={data.progress_timeline} />
            </PlaceholderCard>

            <PlaceholderCard title="Предметы">
              {data.subjects.length === 0 ? (
                <p className="muted">Пока нет проверенных работ</p>
              ) : (
                <div className="subject-grid">
                  {data.subjects.map((s) => (
                    <div
                      key={s.subject_id}
                      className={`subject-card subject-card--${s.level}`}
                    >
                      <div className="subject-card__head">
                        <h4>{s.subject_name}</h4>
                        <span className="subject-card__grade">
                          {s.average_grade}
                        </span>
                      </div>
                      <span className={`badge badge--${s.level}`}>
                        {LEVEL_LABEL[s.level]}
                      </span>
                      <p className="muted">
                        Работ: {s.works_count} · Последняя оценка:{' '}
                        {s.last_grade ?? '—'}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </PlaceholderCard>

            <PlaceholderCard title="Последние работы">
              {data.recent_works.length === 0 ? (
                <p className="muted">Вы ещё не отправляли работы</p>
              ) : (
                <ul className="list">
                  {data.recent_works.map((w) => (
                    <li key={w.id} className="list__item list__item--column">
                      <div className="list__item-row">
                        <span>
                          {w.subject_name} ·{' '}
                          {new Date(w.submitted_at).toLocaleDateString()}
                        </span>
                        <span className="badge">
                          {w.grade != null
                            ? `Оценка: ${w.grade}`
                            : STATUS_LABEL[w.status]}
                        </span>
                      </div>
                      {w.ai_comment && (
                        <p className="muted profile-comment">{w.ai_comment}</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </PlaceholderCard>
          </>
        )}
      </AsyncState>
    </div>
  );
}
