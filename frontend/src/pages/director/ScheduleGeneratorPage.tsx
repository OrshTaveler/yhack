import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

export function ScheduleGeneratorPage() {
  return (
    <div className="page">
      <PageHeader
        title="Генерация расписания"
        description="Укажите классы, обязательные предметы и часы в неделю — ИИ сформирует расписание"
        actions={
          <button type="button" className="btn btn--primary">
            Сгенерировать
          </button>
        }
      />
      <div className="form-grid">
        <PlaceholderCard title="Классы">
          <p className="muted">Список классов (например, 5А, 6Б) — CRUD через API</p>
          <button type="button" className="btn btn--secondary">
            + Добавить класс
          </button>
        </PlaceholderCard>
        <PlaceholderCard title="Предметы и нагрузка">
          <p className="muted">Предмет + часов в неделю на класс</p>
          <button type="button" className="btn btn--secondary">
            + Добавить предмет
          </button>
        </PlaceholderCard>
        <PlaceholderCard title="Ограничения">
          <p className="muted">Кабинеты, окна, совмещения — опционально</p>
        </PlaceholderCard>
      </div>
    </div>
  );
}
