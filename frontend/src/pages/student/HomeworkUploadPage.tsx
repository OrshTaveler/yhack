import { type FormEvent, useState } from 'react';
import { api } from '@/api/client';
import { AsyncState } from '@/components/common/AsyncState';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { useFetch } from '@/hooks/useFetch';

const STATUS_LABEL: Record<string, string> = {
  pending: 'На проверке ИИ',
  ai_reviewed: 'Проверено ИИ',
  teacher_reviewed: 'Оценено учителем',
};

export function HomeworkUploadPage() {
  const { data, loading, error, reload } = useFetch(() => api.homework.listMy(), []);
  const { data: subjectsData } = useFetch(() => api.subjects.list(), []);
  const [subjectId, setSubjectId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const subjects = subjectsData?.items ?? [];
  const items = data?.items ?? [];

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setUploadError(null);
    setUploadSuccess(false);
    const form = e.currentTarget;
    const fileInput = form.elements.namedItem('file') as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (!file || !subjectId) {
      setUploadError('Выберите предмет и файл');
      return;
    }
    const fd = new FormData();
    fd.append('subject_id', subjectId);
    fd.append('file', file);
    setUploading(true);
    try {
      await api.homework.upload(fd);
      setUploadSuccess(true);
      form.reset();
      setSubjectId('');
      await reload();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Ошибка загрузки');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page">
      <PageHeader
        title="Домашние задания"
        description="Загрузите фотографию работы — после проверки ИИ она появится у учителя"
      />
      <PlaceholderCard title="Новая работа">
        <form className="upload-form" onSubmit={(e) => void handleSubmit(e)}>
          <label>
            Предмет
            <select
              className="input"
              required
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
            >
              <option value="" disabled>
                Выберите предмет
              </option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Фотография работы
            <input type="file" name="file" accept="image/*" className="input" required />
          </label>
          {uploadError && <p className="auth-alert">{uploadError}</p>}
          {uploadSuccess && <p className="muted">Работа отправлена на проверку</p>}
          <button type="submit" className="btn btn--primary" disabled={uploading}>
            {uploading ? 'Отправка…' : 'Отправить на проверку'}
          </button>
        </form>
      </PlaceholderCard>
      <PlaceholderCard title="Мои отправленные работы">
        <AsyncState
          loading={loading}
          error={error}
          empty={items.length === 0}
          emptyText="Вы ещё не отправляли работы"
        >
          <ul className="list">
            {items.map((item) => (
              <li key={item.id} className="list__item">
                <span>
                  {item.subject_name} · {new Date(item.submitted_at).toLocaleDateString()}
                </span>
                <span className="badge">
                  {item.teacher_grade != null
                    ? `Оценка: ${item.teacher_grade}`
                    : item.ai_grade != null
                      ? `ИИ: ${item.ai_grade}`
                      : STATUS_LABEL[item.status]}
                </span>
              </li>
            ))}
          </ul>
        </AsyncState>
      </PlaceholderCard>
    </div>
  );
}
