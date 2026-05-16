import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';

export function StudentDashboard() {
  return (
    <div className="page">
      <PageHeader
        title="Кабинет ученика"
        description="Загрузка домашних работ и просмотр оценок"
      />
      <div className="dashboard-grid">
        <Link to="/student/profile" className="dashboard-tile">
          <h3>Мой профиль</h3>
          <p>Прогресс, сильные и слабые темы, история работ</p>
        </Link>
        <Link to="/student/homework" className="dashboard-tile">
          <h3>Домашние задания</h3>
          <p>Загрузите фото работы — ИИ проверит и отправит учителю</p>
        </Link>
        <Link to="/student/grades" className="dashboard-tile">
          <h3>Мои оценки</h3>
          <p>Оценки ИИ и учителя по сданным работам</p>
        </Link>
        <Link to="/schedule" className="dashboard-tile">
          <h3>Расписание</h3>
          <p>Ваше недельное расписание</p>
        </Link>
      </div>
    </div>
  );
}
