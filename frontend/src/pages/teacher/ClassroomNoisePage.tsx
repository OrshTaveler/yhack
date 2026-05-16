import { useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';

export function ClassroomNoisePage() {
  const [recording, setRecording] = useState(false);

  return (
    <div className="page">
      <PageHeader
        title="Анализ шума в классе"
        description="Только для учителя: запись урока, визуализация шума, отчёт в конце занятия"
        actions={
          <button
            type="button"
            className={`btn ${recording ? 'btn--danger' : 'btn--primary'}`}
            onClick={() => setRecording((v) => !v)}
          >
            {recording ? 'Остановить анализ' : 'Начать анализ урока'}
          </button>
        }
      />
      <div className="form-grid">
        <PlaceholderCard title="Уровень шума в реальном времени">
          <div
            className={`recording-indicator${recording ? ' recording-indicator--active' : ''}`}
          >
            {recording ? 'Идёт запись…' : 'Запись не активна'}
          </div>
          <div className="chart-placeholder" aria-hidden />
        </PlaceholderCard>
        <PlaceholderCard title="Самые громкие ученики">
          <table className="data-table">
            <thead>
              <tr>
                <th>Ученик</th>
                <th>Ср. дБ</th>
                <th>Пик дБ</th>
                <th>Инциденты</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={4} className="muted">
                  Данные появятся после анализа
                </td>
              </tr>
            </tbody>
          </table>
        </PlaceholderCard>
        <PlaceholderCard title="Выжимка урока">
          <p className="muted">
            По завершении урока ИИ сформирует краткий отчёт и отправит его вам, а также
            отмеченным ученикам.
          </p>
          <button type="button" className="btn btn--secondary" disabled={recording}>
            Отправить отчёт
          </button>
        </PlaceholderCard>
      </div>
    </div>
  );
}
