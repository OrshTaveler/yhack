import { useState } from 'react';
import { api } from '@/api/client';
import { AsyncState } from '@/components/common/AsyncState';
import { LabeledField } from '@/components/common/LabeledField';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { StatCard } from '@/components/common/StatCard';
import { useFetch } from '@/hooks/useFetch';

export function ClassStatisticsPage() {
  const { data: stats, loading: statsLoading, error: statsError } = useFetch(
    () => api.stats.teacherOverview(),
    [],
  );
  const [classId, setClassId] = useState('');
  const {
    data: grades,
    loading: gradesLoading,
    error: gradesError,
  } = useFetch(
    () => (classId ? api.stats.studentGrades(classId) : Promise.resolve({ items: [] })),
    [classId],
  );

  const classes = stats?.classes ?? [];
  const selectedClass = classes.find((c) => c.class_id === classId);

  return (
    <div className="page">
      <PageHeader
        title="Статистика по классам"
        description="Оценки каждого ученика, его работы и успеваемость"
      />
      <PlaceholderCard title="Мои классы">
        <AsyncState loading={statsLoading} error={statsError} empty={classes.length === 0}>
          <LabeledField label="Выберите класс" hint="Статистика загрузится после выбора">
            <select
              className="input"
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
            >
              <option value="">— не выбран —</option>
              {classes.map((c) => (
                <option key={c.class_id} value={c.class_id}>
                  {c.class_name}
                </option>
              ))}
            </select>
          </LabeledField>
        </AsyncState>
      </PlaceholderCard>
      <div className="form-grid">
        <PlaceholderCard title="Сводка по классу">
          {selectedClass ? (
            <div className="stats-row">
              <StatCard
                value={selectedClass.average_grade || '—'}
                label="Средний балл по классу"
                unit="по шкале 2–5"
              />
              <StatCard
                value={selectedClass.students_count}
                label="Учеников в классе"
                unit="чел."
              />
              <StatCard
                value={selectedClass.pending_homeworks}
                label="Работ на проверке"
                unit="шт."
              />
            </div>
          ) : (
            <p className="muted">Выберите класс в списке выше</p>
          )}
        </PlaceholderCard>
        <PlaceholderCard title="Ученики и оценки">
          <AsyncState
            loading={gradesLoading && !!classId}
            error={gradesError}
            empty={!!classId && !grades?.items.length}
            emptyText="Нет данных по оценкам"
          >
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Ученик</th>
                    <th>Предмет</th>
                    <th>Ср. балл (2–5)</th>
                    <th>Сдано работ, шт.</th>
                  </tr>
                </thead>
                <tbody>
                  {(grades?.items ?? []).map((row) => (
                    <tr key={`${row.student_id}-${row.subject_id}`}>
                      <td>{row.student_name}</td>
                      <td>{row.subject_name}</td>
                      <td>{row.average_grade}</td>
                      <td>{row.works_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </AsyncState>
        </PlaceholderCard>
      </div>
    </div>
  );
}
