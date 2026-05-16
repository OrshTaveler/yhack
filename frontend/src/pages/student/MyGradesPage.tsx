import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

export function MyGradesPage() {
  return (
    <div className="page">
      <PageHeader title="Мои оценки" description="Оценки по сданным домашним работам" />
      <PlaceholderCard title="История оценок">
        <table className="data-table">
          <thead>
            <tr>
              <th>Предмет</th>
              <th>Дата</th>
              <th>ИИ</th>
              <th>Учитель</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td colSpan={5} className="muted">
                Пока нет проверенных работ
              </td>
            </tr>
          </tbody>
        </table>
      </PlaceholderCard>
    </div>
  );
}
