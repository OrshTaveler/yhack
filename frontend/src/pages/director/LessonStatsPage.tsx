import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

export function LessonStatsPage() {
  return (
    <div className="page">
      <PageHeader
        title="Статистика уроков"
        description="Уровень шума в классе и краткая выжимка по завершённым урокам"
      />
      <div className="form-grid">
        <PlaceholderCard title="Список уроков">
          <ul className="list">
            <li className="list__item list__item--clickable">
              <span>5А · Математика · 14.05 10:00</span>
              <span className="badge">Готово</span>
            </li>
          </ul>
        </PlaceholderCard>
        <PlaceholderCard title="Детали урока">
          <p className="muted">График уровня шума по времени</p>
          <div className="chart-placeholder" aria-hidden />
          <h3>Выжимка</h3>
          <p className="muted">
            После выбора урока здесь отобразится краткий отчёт ИИ для директора.
          </p>
        </PlaceholderCard>
      </div>
    </div>
  );
}
