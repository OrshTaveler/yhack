import { useState } from 'react';
import { api } from '@/api/client';
import { AsyncState } from '@/components/common/AsyncState';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { useFetch } from '@/hooks/useFetch';

export function TeacherAssignmentPage() {
  const { data, loading, error, reload } = useFetch(() => api.classes.list(), []);
  const { data: teachersData } = useFetch(() => api.users.list('teacher'), []);
  const [pending, setPending] = useState<Record<string, string>>({});
  const [savingId, setSavingId] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const classes = data?.items ?? [];
  const teachers = teachersData?.items ?? [];

  const save = async (classId: string) => {
    const teacherId = pending[classId];
    if (!teacherId) return;
    setSavingId(classId);
    setSaveError(null);
    try {
      await api.classes.assignTeacher(classId, teacherId);
      await reload();
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : 'Ошибка сохранения');
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="page">
      <PageHeader
        title="Назначение классов"
        description="Назначьте класс ответственному преподавателю"
      />
      {saveError && <div className="auth-alert">{saveError}</div>}
      <PlaceholderCard title="Таблица назначений">
        <AsyncState loading={loading} error={error} empty={classes.length === 0}>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Класс</th>
                  <th>Учитель</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {classes.map((cg) => (
                  <tr key={cg.id}>
                    <td>{cg.name}</td>
                    <td>
                      <select
                        className="input"
                        value={pending[cg.id] ?? cg.teacher_id ?? ''}
                        onChange={(e) =>
                          setPending((p) => ({ ...p, [cg.id]: e.target.value }))
                        }
                      >
                        <option value="">Выберите учителя</option>
                        {teachers.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn--secondary btn--sm"
                        disabled={savingId === cg.id}
                        onClick={() => void save(cg.id)}
                      >
                        {savingId === cg.id ? '…' : 'Сохранить'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </AsyncState>
      </PlaceholderCard>
    </div>
  );
}
