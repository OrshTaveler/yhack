import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

export function HomeworkUploadPage() {
  return (
    <div className="page">
      <PageHeader
        title="Домашние задания"
        description="Загрузите фотографию работы — после проверки ИИ она появится у учителя"
      />
      <PlaceholderCard title="Новая работа">
        <form
          className="upload-form"
          onSubmit={(e) => {
            e.preventDefault();
          }}
        >
          <label>
            Предмет
            <select className="input" required defaultValue="">
              <option value="" disabled>
                Выберите предмет
              </option>
            </select>
          </label>
          <label>
            Фотография работы
            <input type="file" accept="image/*" className="input" required />
          </label>
          <button type="submit" className="btn btn--primary">
            Отправить на проверку
          </button>
        </form>
      </PlaceholderCard>
      <PlaceholderCard title="Мои отправленные работы">
        <ul className="list">
          <li className="list__item">
            <span>Алгебра · 14.05</span>
            <span className="badge">На проверке ИИ</span>
          </li>
        </ul>
      </PlaceholderCard>
    </div>
  );
}
