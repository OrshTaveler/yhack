import type { ScheduleSlotDto } from '@/api/types';

const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

interface ScheduleGridProps {
  slots: ScheduleSlotDto[];
  daysCount?: number;
  periodsCount?: number;
}

export function ScheduleGrid({ slots, daysCount = 5, periodsCount = 6 }: ScheduleGridProps) {
  const days = DAYS.slice(0, daysCount);
  const periods = Array.from({ length: periodsCount }, (_, i) => i + 1);

  const cell = (day: number, period: number) => {
    const found = slots.filter((s) => s.day_of_week === day && s.period === period);
    if (found.length === 0) return '—';
    return found
      .map((s) => `${s.subject_name}${s.class_name ? ` (${s.class_name})` : ''}`)
      .join(', ');
  };

  return (
    <div className="table-scroll">
      <table className="schedule-table">
        <thead>
          <tr>
            <th>Урок</th>
            {days.map((d) => (
              <th key={d}>{d}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {periods.map((period) => (
            <tr key={period}>
              <td>{period}</td>
              {days.map((_, dayIdx) => (
                <td key={dayIdx} className="schedule-table__cell schedule-table__filled">
                  {cell(dayIdx, period)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
