import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';

export function TeacherDashboard() {
  return (
    <div className="page">
      <PageHeader
        title="Кабинет учителя"
        description="Проверка работ, анализ дисциплины и статистика по классам"
      />
      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-card__value">—</span>
          <span className="stat-card__label">Работ на проверке</span>
        </div>
        <div className="stat-card">
          <span className="stat-card__value">—</span>
          <span className="stat-card__label">Моих классов</span>
        </div>
        <div className="stat-card">
          <span className="stat-card__value">—</span>
          <span className="stat-card__label">Средний балл</span>
        </div>
      </div>
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
