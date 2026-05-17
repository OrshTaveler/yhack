import { api } from '@/api/client';
import { AsyncState } from '@/components/common/AsyncState';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { useFetch } from '@/hooks/useFetch';

export function MyGradesPage() {
  const { data, loading, error } = useFetch(() => api.homework.listMy(), []);
  const items = data?.items ?? [];

  return (
    <div className="page">
      <PageHeader title="Мои оценки" description="Оценки по сданным домашним работам" />
      <PlaceholderCard title="История оценок">
        <AsyncState
          loading={loading}
          error={error}
          empty={items.length === 0}
          emptyText="Пока нет проверенных работ"
        >
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Предмет</th>
                  <th>Дата сдачи</th>
                  <th>Оценка (2–5)</th>
                  <th>Статус проверки</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.subject_name}</td>
                    <td>{new Date(item.submitted_at).toLocaleDateString()}</td>
                    <td>{item.teacher_grade ?? '—'}</td>
                    <td>{item.status}</td>
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
