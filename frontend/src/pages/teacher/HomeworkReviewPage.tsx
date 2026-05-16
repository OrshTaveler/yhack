import { useState } from 'react';
import type { HomeworkDto } from '@/api/types';
import { api } from '@/api/client';
import { AsyncState } from '@/components/common/AsyncState';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { GRADE_MAX, GRADE_MIN } from '@/config/grades';
import { useFetch } from '@/hooks/useFetch';

const STATUS_LABEL: Record<string, string> = {
  pending: 'Ожидает ИИ',
  ai_reviewed: 'Проверено ИИ',
  teacher_reviewed: 'Оценено',
};

export function HomeworkReviewPage() {
  const { data, loading, error, reload } = useFetch(() => api.homework.listForTeacher(), []);
  const [selected, setSelected] = useState<HomeworkDto | null>(null);
  const [grade, setGrade] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const selectItem = (item: HomeworkDto) => {
    setSelected(item);
    setGrade(String(item.teacher_grade ?? item.ai_grade ?? ''));
    setSaveError(null);
  };

  const handleConfirm = async () => {
    if (!selected) return;
    const g = Number(grade);
    if (g < GRADE_MIN || g > GRADE_MAX) {
      setSaveError(`Оценка от ${GRADE_MIN} до ${GRADE_MAX}`);
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await api.homework.confirmGrade(selected.id, g);
      setSelected(updated);
      await reload();
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const items = data?.items ?? [];

  return (
    <div className="page">
      <PageHeader
        title="Проверка домашних работ"
        description="Работы учеников с оценкой ИИ и загруженными фотографиями"
      />
      <div className="homework-layout">
        <PlaceholderCard title="Очередь работ">
          <AsyncState
            loading={loading}
            error={error}
            empty={items.length === 0}
            emptyText="Нет работ на проверке"
          >
            <ul className="list">
              {items.map((item) => (
                <li
                  key={item.id}
                  className={`list__item list__item--clickable${selected?.id === item.id ? ' list__item--active' : ''}`}
                  onClick={() => selectItem(item)}
                >
                  <div>
                    <strong>{item.student_name}</strong>
                    <span className="muted"> · {item.subject_name}</span>
                  </div>
                  {item.ai_grade != null && (
                    <span className="badge badge--ai">ИИ: {item.ai_grade}</span>
                  )}
                </li>
              ))}
            </ul>
          </AsyncState>
        </PlaceholderCard>
        <PlaceholderCard title="Просмотр работы">
          {!selected ? (
            <p className="muted">Выберите работу из списка</p>
          ) : (
            <div className="homework-preview">
              <a href={selected.photo_url} target="_blank" rel="noreferrer">
                <img
                  src={selected.photo_url}
                  alt="Домашняя работа"
                  className="homework-preview__img"
                />
              </a>
              <div className="homework-preview__meta">
                <p>
                  <strong>Ученик:</strong> {selected.student_name}
                </p>
                <p>
                  <strong>Оценка ИИ:</strong> {selected.ai_grade ?? '—'}
                </p>
                <p>
                  <strong>Комментарий ИИ:</strong> {selected.ai_comment ?? '—'}
                </p>
                <p>
                  <strong>Статус:</strong> {STATUS_LABEL[selected.status] ?? selected.status}
                </p>
                <div className="inline-form">
                  <label className="field">
                    <span className="field__label">Ваша оценка</span>
                    <span className="field__hint">По шкале от {GRADE_MIN} до {GRADE_MAX} баллов</span>
                    <input
                      type="number"
                      className="input"
                      min={GRADE_MIN}
                      max={GRADE_MAX}
                      step={0.1}
                      value={grade}
                      onChange={(e) => setGrade(e.target.value)}
                    />
                  </label>
                  <button
                    type="button"
                    className="btn btn--primary"
                    disabled={saving}
                    onClick={() => void handleConfirm()}
                  >
                    {saving ? 'Сохранение…' : 'Подтвердить'}
                  </button>
                </div>
                {saveError && <p className="auth-alert auth-alert--inline">{saveError}</p>}
              </div>
            </div>
          )}
        </PlaceholderCard>
      </div>
    </div>
  );
}
