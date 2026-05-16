import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';

export function DirectorDashboard() {
  return (
    <div className="page">
      <PageHeader
        title="Кабинет директора"
        description="Управление расписанием, назначениями и аналитикой уроков"
      />
      <div className="dashboard-grid">
        <Link to="/director/schedule-generator" className="dashboard-tile">
          <h3>Генерация расписания</h3>
          <p>Классы, предметы, часы в неделю → автоматическое расписание</p>
        </Link>
        <Link to="/director/assignments" className="dashboard-tile">
          <h3>Назначение классов</h3>
          <p>Привязка классов к преподавателям</p>
        </Link>
        <Link to="/director/schedules" className="dashboard-tile">
          <h3>Расписания пользователей</h3>
          <p>Просмотр расписания учителя или ученика</p>
        </Link>
        <Link to="/director/lesson-stats" className="dashboard-tile">
          <h3>Статистика уроков</h3>
          <p>Уровень шума и краткая выжимка по завершённым урокам</p>
        </Link>
      </div>
    </div>
  );
}
