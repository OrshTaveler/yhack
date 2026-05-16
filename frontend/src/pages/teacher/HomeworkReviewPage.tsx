import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

export function HomeworkReviewPage() {
  return (
    <div className="page">
      <PageHeader
        title="Проверка домашних работ"
        description="Работы учеников с оценкой ИИ и загруженными фотографиями"
      />
      <div className="homework-layout">
        <PlaceholderCard title="Очередь работ">
          <ul className="list">
            <li className="list__item list__item--clickable">
              <div>
                <strong>Сидоров М.</strong>
                <span className="muted"> · Алгебра</span>
              </div>
              <span className="badge badge--ai">ИИ: 4</span>
            </li>
          </ul>
        </PlaceholderCard>
        <PlaceholderCard title="Просмотр работы">
          <div className="homework-preview">
            <div className="homework-preview__photo">Фото домашки</div>
            <div className="homework-preview__meta">
              <p>
                <strong>Оценка ИИ:</strong> —
              </p>
              <p>
                <strong>Комментарий ИИ:</strong> —
              </p>
              <p>
                <strong>Доп. вопросы:</strong> —
              </p>
              <div className="inline-form">
                <label>
                  Ваша оценка
                  <input type="number" className="input" min={1} max={5} />
                </label>
                <button type="button" className="btn btn--primary">
                  Подтвердить
                </button>
              </div>
            </div>
          </div>
        </PlaceholderCard>
      </div>
    </div>
  );
}
