import { useState } from 'react';
import { api } from '@/api/client';
import type { ScheduleGeneratePayload } from '@/api/types';
import { LabeledField } from '@/components/common/LabeledField';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid';
import {
  parseGradeFromClassName,
  STUDENTS_COUNT_MAX,
  STUDENTS_COUNT_MIN,
} from '@/config/className';

type ClassRow = { name: string; students_count: number };
type SubjectRow = { subject_name: string; hours_per_week: number };

export function ScheduleGeneratorPage() {
  const [classes, setClasses] = useState<ClassRow[]>([{ name: '5А', students_count: 25 }]);
  const [subjects, setSubjects] = useState<SubjectRow[]>([
    { subject_name: 'Математика', hours_per_week: 4 },
    { subject_name: 'Алгебра', hours_per_week: 3 },
  ]);
  const [result, setResult] = useState<Awaited<ReturnType<typeof api.schedule.generate>> | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: ScheduleGeneratePayload = { classes, subjects };
      const res = await api.schedule.generate(payload);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка генерации');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <PageHeader
        title="Генерация расписания"
        description="Укажите классы, предметы и часы в неделю"
        actions={
          <button
            type="button"
            className="btn btn--primary"
            disabled={loading}
            onClick={() => void generate()}
          >
            {loading ? 'Генерация…' : 'Сгенерировать'}
          </button>
        }
      />
      {error && <div className="auth-alert">{error}</div>}
      <div className="form-grid">
        <PlaceholderCard title="Классы">
          {classes.map((c, i) => {
            const parsedGrade = parseGradeFromClassName(c.name);
            return (
              <div key={i} className="form-row form-row--2">
                <LabeledField
                  label="Название класса"
                  hint={
                    parsedGrade != null
                      ? `Параллель: ${parsedGrade} (из названия)`
                      : 'Например: 5А, 10Б — параллель берётся из цифр в начале'
                  }
                >
                  <input
                    className="input"
                    placeholder="5А"
                    value={c.name}
                    onChange={(e) => {
                      const next = [...classes];
                      next[i] = { ...next[i], name: e.target.value };
                      setClasses(next);
                    }}
                  />
                </LabeledField>
                <LabeledField
                  label="Количество учеников"
                  hint={`От ${STUDENTS_COUNT_MIN} до ${STUDENTS_COUNT_MAX}`}
                >
                  <input
                    type="number"
                    className="input"
                    min={STUDENTS_COUNT_MIN}
                    max={STUDENTS_COUNT_MAX}
                    value={c.students_count}
                    onChange={(e) => {
                      const next = [...classes];
                      next[i] = {
                        ...next[i],
                        students_count: Number(e.target.value),
                      };
                      setClasses(next);
                    }}
                  />
                </LabeledField>
              </div>
            );
          })}
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() =>
              setClasses([...classes, { name: '', students_count: 25 }])
            }
          >
            + Добавить класс
          </button>
        </PlaceholderCard>
        <PlaceholderCard title="Предметы и нагрузка">
          {subjects.map((s, i) => (
            <div key={i} className="form-row form-row--2">
              <LabeledField label="Название предмета">
                <input
                  className="input"
                  placeholder="Математика"
                  value={s.subject_name}
                  onChange={(e) => {
                    const next = [...subjects];
                    next[i] = { ...next[i], subject_name: e.target.value };
                    setSubjects(next);
                  }}
                />
              </LabeledField>
              <LabeledField label="Часов в неделю" hint="Уроков на класс за неделю">
                <input
                  type="number"
                  className="input"
                  min={1}
                  max={40}
                  value={s.hours_per_week}
                  onChange={(e) => {
                    const next = [...subjects];
                    next[i] = { ...next[i], hours_per_week: Number(e.target.value) };
                    setSubjects(next);
                  }}
                />
              </LabeledField>
            </div>
          ))}
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() =>
              setSubjects([...subjects, { subject_name: '', hours_per_week: 2 }])
            }
          >
            + Добавить предмет
          </button>
        </PlaceholderCard>
      </div>
      {result && (
        <PlaceholderCard title="Результат">
          <ScheduleGrid slots={result.slots} />
        </PlaceholderCard>
      )}
    </div>
  );
}
