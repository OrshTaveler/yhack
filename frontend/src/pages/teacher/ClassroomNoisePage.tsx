import { useEffect, useRef, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { StatCard } from '@/components/common/StatCard';
import {
  MOCK_HOMEWORK,
  MOCK_NOISE,
  MOCK_STUDENTS,
  MOCK_SUMMARY,
  type BehaviorStatus,
  type NoiseSample,
} from './mockLesson';

// ── Пороги уровня шума (дБ) ──────────────────────────────
function noiseLevel(db: number): { label: string; cls: string } {
  if (db < 50) return { label: 'Тихо', cls: 'quiet' };
  if (db < 65) return { label: 'Рабочий шум', cls: 'normal' };
  return { label: 'Шумно', cls: 'loud' };
}

const BEHAVIOR_META: Record<BehaviorStatus, { label: string; cls: string }> = {
  active: { label: 'Работал активно', cls: 'strong' },
  normal: { label: 'Работал спокойно', cls: 'normal' },
  distracted: { label: 'Отвлекался', cls: 'normal' },
  noisy: { label: 'Мешал на уроке', cls: 'weak' },
};

// ── Поминутный график шума (столбики) ────────────────────
function NoiseChart({ samples }: { samples: NoiseSample[] }) {
  const max = 80;
  const min = 35;
  return (
    <div className="noise-chart">
      {samples.map((s) => {
        const h = ((s.level_db - min) / (max - min)) * 100;
        return (
          <div
            key={s.minute}
            className={`noise-bar noise-bar--${noiseLevel(s.level_db).cls}`}
            style={{ height: `${Math.max(4, h)}%` }}
            title={`${s.minute} мин — ${s.level_db} дБ (${noiseLevel(s.level_db).label})`}
          />
        );
      })}
    </div>
  );
}

// ── Живой индикатор шума (во время записи) ───────────────
function LiveIndicator({ db }: { db: number }) {
  const lvl = noiseLevel(db);
  return (
    <div className={`noise-live noise-live--${lvl.cls}`}>
      <span className="noise-live__value">{db}</span>
      <span className="noise-live__unit">дБ</span>
      <span className="noise-live__label">{lvl.label}</span>
    </div>
  );
}

export function ClassroomNoisePage() {
  const [phase, setPhase] = useState<'idle' | 'recording' | 'report'>('idle');
  const [elapsed, setElapsed] = useState(0); // секунды записи
  const [liveDb, setLiveDb] = useState(46);
  const timerRef = useRef<number | null>(null);

  // Имитация живого уровня шума во время записи (МОК)
  useEffect(() => {
    if (phase !== 'recording') return;
    const timer = window.setInterval(() => {
      setElapsed((e) => e + 1);
      // случайное блуждание 40..75 дБ
      setLiveDb((d) => {
        const next = d + (Math.random() * 16 - 8);
        return Math.round(Math.min(75, Math.max(40, next)));
      });
    }, 1000);
    timerRef.current = timer;
    return () => window.clearInterval(timer);
  }, [phase]);

  const start = () => {
    setElapsed(0);
    setLiveDb(46);
    setPhase('recording');
  };
  const stop = () => setPhase('report');
  const reset = () => setPhase('idle');

  // ── Метрики отчёта (МОК-расчёт по MOCK_NOISE) ──────────
  const avgNoise = Math.round(
    MOCK_NOISE.reduce((s, n) => s + n.level_db, 0) / MOCK_NOISE.length,
  );
  const peakNoise = Math.max(...MOCK_NOISE.map((n) => n.level_db));
  const loudMinutes = MOCK_NOISE.filter((n) => n.level_db >= 65).length;

  return (
    <div className="page">
      <PageHeader
        title="Анализ урока"
        description="Запись шума, поведение класса и тезисы урока"
        actions={
          phase === 'recording' ? (
            <button type="button" className="btn btn--danger" onClick={stop}>
              Завершить урок
            </button>
          ) : phase === 'report' ? (
            <button type="button" className="btn" onClick={reset}>
              Новый урок
            </button>
          ) : (
            <button type="button" className="btn btn--primary" onClick={start}>
              Начать урок
            </button>
          )
        }
      />

      {/* ─── ОЖИДАНИЕ ─── */}
      {phase === 'idle' && (
        <PlaceholderCard title="Запись не активна">
          <p className="muted">
            Нажмите «Начать урок» — система будет отслеживать уровень шума, а в
            конце сформирует отчёт: поведение учеников, тезисы и домашнее задание.
          </p>
        </PlaceholderCard>
      )}

      {/* ─── ЗАПИСЬ ─── */}
      {phase === 'recording' && (
        <div className="form-grid">
          <PlaceholderCard title="Уровень шума сейчас">
            <LiveIndicator db={liveDb} />
          </PlaceholderCard>
          <PlaceholderCard title="Идёт запись урока">
            <p className="recording-indicator recording-indicator--active">
              🔴 Запись · {Math.floor(elapsed / 60)} мин {elapsed % 60} сек
            </p>
            <p className="muted">
              Алиса слушает урок. По завершении сформирует отчёт по классу.
            </p>
          </PlaceholderCard>
        </div>
      )}

      {/* ─── ОТЧЁТ ─── */}
      {phase === 'report' && (
        <>
          <div className="stats-row">
            <StatCard value={avgNoise} label="Средний шум" unit="дБ" />
            <StatCard value={peakNoise} label="Пик шума" unit="дБ" />
            <StatCard value={loudMinutes} label="Шумных минут" unit="мин" />
          </div>

          <PlaceholderCard title="Уровень шума поминутно">
            <NoiseChart samples={MOCK_NOISE} />
            <div className="noise-legend">
              <span><i className="dot dot--quiet" /> тихо (&lt;50)</span>
              <span><i className="dot dot--normal" /> рабочий шум (50–65)</span>
              <span><i className="dot dot--loud" /> шумно (&gt;65)</span>
            </div>
          </PlaceholderCard>

          <PlaceholderCard title="Поведение учеников">
            <ul className="list">
              {MOCK_STUDENTS.map((s) => (
                <li key={s.name} className="list__item list__item--column">
                  <div className="list__item-row">
                    <span>{s.name}</span>
                    <span className={`badge badge--${BEHAVIOR_META[s.status].cls}`}>
                      {BEHAVIOR_META[s.status].label}
                    </span>
                  </div>
                  <p className="muted profile-comment">{s.note}</p>
                </li>
              ))}
            </ul>
          </PlaceholderCard>

          <div className="form-grid">
            <PlaceholderCard title="Тезисы урока">
              <ul className="bullet-list">
                {MOCK_SUMMARY.map((line, i) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            </PlaceholderCard>
            <PlaceholderCard title="Домашнее задание">
              <p>{MOCK_HOMEWORK}</p>
              <p className="muted">Выделено по ключевым словам в речи учителя</p>
            </PlaceholderCard>
          </div>
        </>
      )}
    </div>
  );
}
