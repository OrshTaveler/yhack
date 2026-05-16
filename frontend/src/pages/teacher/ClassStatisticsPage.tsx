import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

export function ClassStatisticsPage() {
  return (
    <div className="page">
      <PageHeader
        title="Статистика по классам"
        description="Оценки каждого ученика, его работы и успеваемость"
      />
      <PlaceholderCard title="Мои классы">
        <div className="inline-form">
          <select className="input" defaultValue="">
            <option value="">Выберите класс</option>
          </select>
        </div>
      </PlaceholderCard>
      <div className="form-grid">
        <PlaceholderCard title="Сводка по классу">
          <div className="stats-row">
            <div className="stat-card">
              <span className="stat-card__value">—</span>
              <span className="stat-card__label">Средний балл</span>
            </div>
            <div className="stat-card">
              <span className="stat-card__value">—</span>
              <span className="stat-card__label">Учеников</span>
            </div>
          </div>
        </PlaceholderCard>
        <PlaceholderCard title="Ученики и оценки">
          <table className="data-table">
            <thead>
              <tr>
                <th>Ученик</th>
                <th>Предмет</th>
                <th>Ср. балл</th>
                <th>Работ</th>
                <th />
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={5} className="muted">
                  Выберите класс для загрузки данных
                </td>
              </tr>
            </tbody>
          </table>
        </PlaceholderCard>
      </div>
    </div>
  );
}
