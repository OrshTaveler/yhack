import { useState } from 'react';
import { api } from '@/api/client';
import { AsyncState } from '@/components/common/AsyncState';
import { LabeledField } from '@/components/common/LabeledField';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid';
import { useFetch } from '@/hooks/useFetch';

export function UserSchedulesPage() {
  const [role, setRole] = useState<'teacher' | 'student'>('teacher');
  const { data: users, loading: usersLoading } = useFetch(
    () => api.users.list(role),
    [role],
  );
  const [userId, setUserId] = useState('');
  const [show, setShow] = useState(false);
  const {
    data: schedule,
    loading: schedLoading,
    error: schedError,
  } = useFetch(
    () => (show && userId ? api.schedule.getForUser(userId) : Promise.resolve({ slots: [] })),
    [show, userId],
  );

  const userList = users?.items ?? [];

  return (
    <div className="page">
      <PageHeader
        title="Расписания пользователей"
        description="Просмотр расписания любого учителя или ученика"
      />
      <PlaceholderCard title="Поиск пользователя">
        <div className="inline-form">
          <LabeledField label="Роль пользователя">
            <select
              className="input"
              value={role}
              onChange={(e) => {
                setRole(e.target.value as 'teacher' | 'student');
                setUserId('');
                setShow(false);
              }}
            >
              <option value="teacher">Учитель</option>
              <option value="student">Ученик</option>
            </select>
          </LabeledField>
          <LabeledField label="Пользователь" hint="ФИО и email в списке">
            <select
              className="input"
              value={userId}
              disabled={usersLoading}
              onChange={(e) => {
                setUserId(e.target.value);
                setShow(false);
              }}
            >
              <option value="">Выберите пользователя</option>
              {userList.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.email})
                </option>
              ))}
            </select>
          </LabeledField>
          <button
            type="button"
            className="btn btn--primary"
            disabled={!userId}
            onClick={() => setShow(true)}
          >
            Показать расписание
          </button>
        </div>
      </PlaceholderCard>
      {show && (
        <PlaceholderCard title="Расписание">
          <AsyncState
            loading={schedLoading}
            error={schedError}
            empty={!schedule?.slots.length}
            emptyText="Расписание пустое"
          >
            <ScheduleGrid slots={schedule!.slots} />
          </AsyncState>
        </PlaceholderCard>
      )}
    </div>
  );
}
