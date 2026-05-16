import { Link } from 'react-router-dom';
import { api } from '@/api/client';
import { AsyncState } from '@/components/common/AsyncState';
import { PageHeader } from '@/components/common/PageHeader';
import { StatCard } from '@/components/common/StatCard';
import { useFetch } from '@/hooks/useFetch';

export function TeacherDashboard() {
  const { data, loading, error } = useFetch(() => api.stats.teacherOverview(), []);

  return (
    <div className="page">
      <PageHeader
        title="Кабинет учителя"
        description="Проверка работ, анализ дисциплины и статистика по классам"
      />
      <AsyncState loading={loading} error={error}>
        {data && (
          <div className="stats-row">
            <StatCard
              value={data.pending_homeworks}
              label="Работ на проверке"
              unit="шт."
            />
            <StatCard value={data.classes_count} label="Моих классов" unit="шт." />
            <StatCard
              value={data.average_grade || '—'}
              label="Средний балл"
              unit="по шкале 2–5"
            />
          </div>
        )}
      </AsyncState>
      <div className="dashboard-grid">
        <Link to="/teacher/homework" className="dashboard-tile">
          <h3>Проверка домашних работ</h3>
          <p>Оценка ИИ, фото работы, подтверждение или правка оценки</p>
        </Link>
        <Link to="/teacher/noise" className="dashboard-tile">
          <h3>Анализ шума в классе</h3>
          <p>Запись урока, статистика, выжимка в конце занятия</p>
        </Link>
        <Link to="/teacher/statistics" className="dashboard-tile">
          <h3>Статистика</h3>
          <p>Оценки учеников, работы, успеваемость по классам</p>
        </Link>
      </div>
    </div>
  );
}
