import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

export function TeacherAssignmentPage() {
  return (
    <div className="page">
      <PageHeader
        title="Назначение классов"
        description="Назначьте класс ответственному преподавателю"
      />
      <PlaceholderCard title="Таблица назначений">
        <table className="data-table">
          <thead>
            <tr>
              <th>Класс</th>
              <th>Учитель</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>5А</td>
              <td>
                <select className="input" defaultValue="">
                  <option value="">Выберите учителя</option>
                </select>
              </td>
              <td>
                <button type="button" className="btn btn--secondary btn--sm">
                  Сохранить
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </PlaceholderCard>
    </div>
  );
}
