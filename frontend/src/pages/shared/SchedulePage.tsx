import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт'];
const PERIODS = [1, 2, 3, 4, 5, 6];

export function SchedulePage() {
  return (
    <div className="page">
      <PageHeader
        title="Расписание"
        description="Ваше недельное расписание. Директор может просматривать расписание любого пользователя."
      />
      <PlaceholderCard title="Сетка расписания">
        <table className="schedule-table">
          <thead>
            <tr>
              <th>Урок</th>
              {DAYS.map((d) => (
                <th key={d}>{d}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {PERIODS.map((period) => (
              <tr key={period}>
                <td>{period}</td>
                {DAYS.map((day) => (
                  <td key={day} className="schedule-table__cell">
                    —
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </PlaceholderCard>
    </div>
  );
}
