import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

export function UserSchedulesPage() {
  return (
    <div className="page">
      <PageHeader
        title="Расписания пользователей"
        description="Просмотр расписания любого учителя или ученика"
      />
      <PlaceholderCard title="Поиск пользователя">
        <div className="inline-form">
          <select className="input" defaultValue="teacher">
            <option value="teacher">Учитель</option>
            <option value="student">Ученик</option>
          </select>
          <select className="input" defaultValue="">
            <option value="">Выберите пользователя</option>
          </select>
          <button type="button" className="btn btn--primary">
            Показать расписание
          </button>
        </div>
      </PlaceholderCard>
    </div>
  );
}
