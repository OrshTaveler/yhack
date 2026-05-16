import { api } from '@/api/client';
import { AsyncState } from '@/components/common/AsyncState';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid';
import { useFetch } from '@/hooks/useFetch';

export function SchedulePage() {
  const { data, loading, error } = useFetch(() => api.schedule.getMy(), []);

  return (
    <div className="page">
      <PageHeader
        title="Расписание"
        description="Ваше недельное расписание"
      />
      <PlaceholderCard title="Сетка расписания">
        <AsyncState
          loading={loading}
          error={error}
          empty={!data?.slots.length}
          emptyText="Расписание пока пустое. Директор может сгенерировать его в разделе «Генерация расписания»."
        >
          {data && <ScheduleGrid slots={data.slots} />}
        </AsyncState>
      </PlaceholderCard>
    </div>
  );
}
