import { type FormEvent, useEffect, useState } from 'react';
import { api } from '@/api/client';
import type { HomeworkDto } from '@/api/types';
import { AsyncState } from '@/components/common/AsyncState';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { useFetch } from '@/hooks/useFetch';

const STATUS_LABEL: Record<string, string> = {
  pending: 'Идёт проверка…',
  ai_reviewed: 'Проверено ИИ',
  teacher_reviewed: 'Оценено учителем',
};

/** Вердикт по уникальности (антиплагиат). */
function plagiarismVerdict(unique: number): { text: string; cls: string } {
  if (unique > 70) return { text: '✅ Написано самостоятельно', cls: 'strong' };
  if (unique >= 40) return { text: '🟡 Частично заимствовано', cls: 'normal' };
  return { text: '🔴 Списано из интернета', cls: 'weak' };
}

/** Вердикт по вероятности AI-генерации. */
function aiVerdict(prob: number): { text: string; cls: string } {
  if (prob >= 70) return { text: '🔴 Похоже на нейросеть', cls: 'weak' };
  if (prob >= 30) return { text: '🟡 Возможна AI-генерация', cls: 'normal' };
  return { text: '✅ Похоже на свою работу', cls: 'strong' };
}

/** Карточка результата проверки одной работы. */
function HomeworkResult({ item }: { item: HomeworkDto }) {
  const [showText, setShowText] = useState(false);

  if (item.status === 'pending') {
    return (
      <div className="hw-result hw-result--pending">
        <span className="recording-indicator recording-indicator--active">
          🔄 Идёт проверка: OCR → антиплагиат → AI-детектор…
        </span>
      </div>
    );
  }

  const unique = item.text_unique;
  const aiProb = item.ai_probability;
  const sources = item.plagiarism_sources ?? [];

  return (
    <div className="hw-result">
      {unique != null && (
        <div className="hw-check">
          <span className={`badge badge--${plagiarismVerdict(unique).cls}`}>
            {plagiarismVerdict(unique).text}
          </span>
          <span className="muted">Уникальность: {unique.toFixed(0)}%</span>
        </div>
      )}

      {aiProb != null && (
        <div className="hw-check">
          <span className={`badge badge--${aiVerdict(aiProb).cls}`}>
            {aiVerdict(aiProb).text}
          </span>
          <span className="muted">
            Вероятность AI: {aiProb.toFixed(0)}%
            {item.ai_detector_reason ? ` — ${item.ai_detector_reason}` : ''}
          </span>
        </div>
      )}

      {sources.length > 0 && (
        <details className="hw-sources">
          <summary>Найдено совпадений: {sources.length}</summary>
          <ul className="list">
            {sources.slice(0, 5).map((s, i) => (
              <li key={i} className="list__item">
                <a href={s.url ?? '#'} target="_blank" rel="noreferrer">
                  {s.url}
                </a>
                <span className="badge">{s.plagiat?.toFixed(0)}%</span>
              </li>
            ))}
          </ul>
        </details>
      )}

      {item.ocr_text && (
        <button
          type="button"
          className="link-btn"
          onClick={() => setShowText((v) => !v)}
        >
          {showText ? 'Скрыть распознанный текст' : 'Показать распознанный текст'}
        </button>
      )}
      {showText && item.ocr_text && (
        <pre className="hw-ocr-text">{item.ocr_text}</pre>
      )}
    </div>
  );
}

export function HomeworkUploadPage() {
  const { data, loading, error, reload } = useFetch(() => api.homework.listMy(), []);
  const { data: subjectsData } = useFetch(() => api.subjects.list(), []);
  const [subjectId, setSubjectId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const subjects = subjectsData?.items ?? [];
  const items = data?.items ?? [];

  // Пока есть работы «в проверке» — опрашиваем сервер каждые 5 сек
  const hasPending = items.some((i) => i.status === 'pending');
  useEffect(() => {
    if (!hasPending) return;
    const timer = setInterval(() => void reload(), 5000);
    return () => clearInterval(timer);
  }, [hasPending, reload]);

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
        description="Загрузите фото работы — ИИ распознает текст, проверит на списывание и AI-генерацию"
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
          {uploadSuccess && (
            <p className="muted">Работа отправлена — проверка займёт до минуты</p>
          )}
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
              <li key={item.id} className="list__item list__item--column">
                <div className="list__item-row">
                  <span>
                    {item.subject_name} ·{' '}
                    {new Date(item.submitted_at).toLocaleDateString()}
                  </span>
                  <span className="badge">
                    {item.teacher_grade != null
                      ? `Оценка: ${item.teacher_grade}`
                      : STATUS_LABEL[item.status]}
                  </span>
                </div>
                <HomeworkResult item={item} />
              </li>
            ))}
          </ul>
        </AsyncState>
      </PlaceholderCard>
    </div>
  );
}
