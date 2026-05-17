import { useEffect, useMemo, useRef, useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { PlaceholderCard } from '@/components/common/PlaceholderCard';
import { StatCard } from '@/components/common/StatCard';

const VOICE_RECOGNITION_URL = 'http://localhost:8001/recognize-voice';
const AUDIO_BUFFER_MS = 5000;
const AUDIO_SEND_INTERVAL_MS = 1000;
const WAV_CHANNELS = 1;
const WAV_BITS_PER_SAMPLE = 16;

// ── Уровни для dBFS, которые возвращает backend ──────────
function noiseLevel(dbfs: number): { label: string; cls: string } {
  if (dbfs < -45) return { label: 'Тихо', cls: 'quiet' };
  if (dbfs < -30) return { label: 'Рабочий шум', cls: 'normal' };
  return { label: 'Шумно', cls: 'loud' };
}

function humanNoiseStatus(result: VoiceRecognitionResponse) {
  if (result.sampled_person_speaking) {
    return 'Говорит учитель';
  }

  if (result.status === 'silence') {
    return 'Тихо, учитель не говорит';
  }

  if (result.status === 'other_speaker_or_unknown') {
    return 'Есть шум, учитель не говорит';
  }

  if (result.status === 'sampled_person_speaking') {
    return 'Говорит учитель';
  }

  return 'Шум, учитель не говорит';
}

declare global {
  interface Window {
    webkitAudioContext?: typeof AudioContext;
  }
}

type VoiceRecognitionResponse = {
  status: string;
  sampled_person_speaking: boolean;
  score: number | null;
  current_dbfs: number;
  background_noise_dbfs: number | null;
  rms: number;
};

type NoisePoint = {
  timestamp: string;
  current_dbfs: number;
  background_noise_dbfs: number | null;
  rms: number;
  status: string;
};

type TimelineEvent = {
  timestampMs: number;
  current_dbfs: number;
  teacher_speaking: boolean;
};

type TimelineMinuteWindow = {
  minute: number;
  start_at: string;
  end_at: string;
  average_loudness_dbfs: number;
  teacher_speaking_percent: number;
  samples_count: number;
};

function buildTimelineJson(
  events: TimelineEvent[],
  startedAtMs: number | null,
): TimelineMinuteWindow[] {
  if (startedAtMs === null) return [];

  const buckets = new Map<
    number,
    { totalDbfs: number; teacherSpeakingCount: number; samplesCount: number }
  >();

  events.forEach((event) => {
    const minute = Math.max(0, Math.floor((event.timestampMs - startedAtMs) / 60000));
    const bucket = buckets.get(minute) ?? {
      totalDbfs: 0,
      teacherSpeakingCount: 0,
      samplesCount: 0,
    };

    bucket.totalDbfs += event.current_dbfs;
    bucket.teacherSpeakingCount += event.teacher_speaking ? 1 : 0;
    bucket.samplesCount += 1;
    buckets.set(minute, bucket);
  });

  return [...buckets.entries()]
    .sort(([a], [b]) => a - b)
    .map(([minute, bucket]) => ({
      minute: minute + 1,
      start_at: new Date(startedAtMs + minute * 60000).toISOString(),
      end_at: new Date(startedAtMs + (minute + 1) * 60000).toISOString(),
      average_loudness_dbfs: Number((bucket.totalDbfs / bucket.samplesCount).toFixed(1)),
      teacher_speaking_percent: Number(
        ((bucket.teacherSpeakingCount / bucket.samplesCount) * 100).toFixed(1),
      ),
      samples_count: bucket.samplesCount,
    }));
}

function writeString(view: DataView, offset: number, value: string) {
  for (let i = 0; i < value.length; i += 1) {
    view.setUint8(offset + i, value.charCodeAt(i));
  }
}

function encodeWav(samples: Float32Array, sampleRate: number) {
  const bytesPerSample = WAV_BITS_PER_SAMPLE / 8;
  const blockAlign = WAV_CHANNELS * bytesPerSample;
  const buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);
  const view = new DataView(buffer);

  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + samples.length * bytesPerSample, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, WAV_CHANNELS, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, WAV_BITS_PER_SAMPLE, true);
  writeString(view, 36, 'data');
  view.setUint32(40, samples.length * bytesPerSample, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i += 1, offset += 2) {
    const sample = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
  }

  return buffer;
}

function arrayBufferToBase64(buffer: ArrayBuffer) {
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  let binary = '';

  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(i, i + chunkSize);
    binary += String.fromCharCode(...chunk);
  }

  return window.btoa(binary);
}

function mergeAudioChunks(chunks: Float32Array[]) {
  const length = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const result = new Float32Array(length);
  let offset = 0;

  chunks.forEach((chunk) => {
    result.set(chunk, offset);
    offset += chunk.length;
  });

  return result;
}

function trimAudioBufferToLastSamples(
  chunks: Float32Array[],
  maxSamples: number,
): { chunks: Float32Array[]; samplesCount: number } {
  const trimmed: Float32Array[] = [];
  let remaining = maxSamples;
  let samplesCount = 0;

  for (let i = chunks.length - 1; i >= 0 && remaining > 0; i -= 1) {
    const chunk = chunks[i];

    if (chunk.length <= remaining) {
      trimmed.unshift(chunk);
      remaining -= chunk.length;
      samplesCount += chunk.length;
      continue;
    }

    const tail = chunk.slice(chunk.length - remaining);
    trimmed.unshift(tail);
    samplesCount += tail.length;
    remaining = 0;
  }

  return { chunks: trimmed, samplesCount };
}

function calculateRms(samples: Float32Array) {
  if (!samples.length) return 0;

  let sum = 0;
  for (let i = 0; i < samples.length; i += 1) {
    sum += samples[i] * samples[i];
  }

  return Math.sqrt(sum / samples.length);
}

async function sendWavChunk(base64: string, sampleRate: number) {
  const response = await fetch(VOICE_RECOGNITION_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      audio_data: base64,
      sample_rate: sampleRate,
    }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Не удалось отправить аудио на анализ');
  }

  return response.json() as Promise<VoiceRecognitionResponse>;
}

// ── Живой индикатор шума во время записи ────────────────
function LiveIndicator({ dbfs }: { dbfs: number | null }) {
  const value = dbfs ?? -100;
  const lvl = noiseLevel(value);

  return (
    <div className={`noise-live noise-live--${lvl.cls}`}>
      <span className="noise-live__value">{Math.round(value)}</span>
      <span className="noise-live__unit">dBFS</span>
      <span className="noise-live__label">{dbfs === null ? 'Ожидание' : lvl.label}</span>
    </div>
  );
}

function NoiseChart({ points }: { points: NoisePoint[] }) {
  if (!points.length) {
    return <div className="chart-placeholder" aria-hidden />;
  }

  const min = -60;
  const max = 0;

  return (
    <div className="noise-chart">
      {points.map((point, index) => {
        const normalized = ((point.current_dbfs - min) / (max - min)) * 100;
        const height = Math.max(4, Math.min(100, normalized));
        const level = noiseLevel(point.current_dbfs);

        return (
          <div
            key={`${point.timestamp}-${index}`}
            className={`noise-bar noise-bar--${level.cls}`}
            style={{ height: `${height}%` }}
            title={`${new Date(point.timestamp).toLocaleTimeString()} — ${point.current_dbfs.toFixed(1)} dBFS (${level.label})`}
          />
        );
      })}
    </div>
  );
}

function formatDuration(seconds: number) {
  return `${Math.floor(seconds / 60)} мин ${seconds % 60} сек`;
}

export function ClassroomNoisePage() {
  const [phase, setPhase] = useState<'idle' | 'recording' | 'report'>('idle');
  const [elapsed, setElapsed] = useState(0);
  const [liveDbfs, setLiveDbfs] = useState<number | null>(null);
  const [processedChunks, setProcessedChunks] = useState(0);
  const [includedChunks, setIncludedChunks] = useState(0);
  const [lastResult, setLastResult] = useState<VoiceRecognitionResponse | null>(null);
  const [noisePoints, setNoisePoints] = useState<NoisePoint[]>([]);
  const [lessonTimelineJson, setLessonTimelineJson] = useState<TimelineMinuteWindow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const timerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const intervalRef = useRef<number | null>(null);
  const audioBufferRef = useRef<Float32Array[]>([]);
  const audioBufferSamplesRef = useRef(0);
  const sampleRateRef = useRef<number>(16000);
  const flushingRef = useRef(false);
  const lessonStartedAtRef = useRef<number | null>(null);
  const timelineEventsRef = useRef<TimelineEvent[]>([]);

  const avgNoise = useMemo(() => {
    if (!noisePoints.length) return null;

    const sum = noisePoints.reduce((acc, point) => acc + point.current_dbfs, 0);
    return sum / noisePoints.length;
  }, [noisePoints]);

  const peakNoise = useMemo(() => {
    if (!noisePoints.length) return null;

    return Math.max(...noisePoints.map((point) => point.current_dbfs));
  }, [noisePoints]);

  const loudChunks = useMemo(() => {
    return noisePoints.filter((point) => point.current_dbfs >= -30).length;
  }, [noisePoints]);

  const saveTimelineEvent = (result: VoiceRecognitionResponse) => {
    const event: TimelineEvent = {
      timestampMs: Date.now(),
      current_dbfs: result.current_dbfs,
      teacher_speaking: result.sampled_person_speaking,
    };

    timelineEventsRef.current = [...timelineEventsRef.current, event];

    // Локально сохраняем JSON таймлайна урока. Пока никуда не отправляем.
    // Формат: окна по 1 минуте, средняя громкость и процент времени, когда говорил учитель.
    const timelineJson = buildTimelineJson(
      timelineEventsRef.current,
      lessonStartedAtRef.current,
    );

    setLessonTimelineJson(timelineJson);
    console.log('Lesson timeline JSON:', timelineJson);
  };

  useEffect(() => {
    if (phase !== 'recording') return;

    const timer = window.setInterval(() => {
      setElapsed((value) => value + 1);
    }, 1000);

    timerRef.current = timer;

    return () => {
      window.clearInterval(timer);
      timerRef.current = null;
    };
  }, [phase]);

  const flushAudioChunk = async () => {
    if (flushingRef.current) return;
    if (!audioBufferRef.current.length) return;

    const sampleRate = sampleRateRef.current;
    const requiredSamples = Math.round(sampleRate * (AUDIO_BUFFER_MS / 1000));

    // Отправляем не накопленный с нуля кусок, а скользящее окно последних 5 секунд.
    // Поэтому буфер не очищается после отправки: он постоянно хранит только свежие 5 секунд.
    if (audioBufferSamplesRef.current < requiredSamples) return;

    const samples = mergeAudioChunks(audioBufferRef.current);

    const localRms = calculateRms(samples);
    if (localRms < 0.001) {
      return;
    }

    flushingRef.current = true;

    try {
      const wavBuffer = encodeWav(samples, sampleRate);
      const base64 = arrayBufferToBase64(wavBuffer);
      const result = await sendWavChunk(base64, sampleRate);

      setProcessedChunks((count) => count + 1);
      setLastResult(result);
      setLiveDbfs(result.current_dbfs);
      saveTimelineEvent(result);

      // В статистику берём только шум, когда учитель не говорит.
      if (!result.sampled_person_speaking) {
        setIncludedChunks((count) => count + 1);
        setNoisePoints((points) => [
          ...points,
          {
            timestamp: new Date().toISOString(),
            current_dbfs: result.current_dbfs,
            background_noise_dbfs: result.background_noise_dbfs,
            rms: result.rms,
            status: result.status,
          },
        ]);
      }
    } catch (e) {
      console.error('Failed to send WAV chunk:', e);
      setError(e instanceof Error ? e.message : 'Не удалось отправить аудио на анализ');
    } finally {
      flushingRef.current = false;
    }
  };

  const stopMicrophone = async () => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    await flushAudioChunk();

    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      await audioContextRef.current.close();
    }

    streamRef.current?.getTracks().forEach((track) => track.stop());

    processorRef.current = null;
    sourceRef.current = null;
    audioContextRef.current = null;
    streamRef.current = null;
    audioBufferRef.current = [];
    audioBufferSamplesRef.current = 0;
  };

  const startMicrophone = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
    const audioContext = new AudioContextConstructor({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, WAV_CHANNELS, WAV_CHANNELS);

    sampleRateRef.current = audioContext.sampleRate;

    processor.onaudioprocess = (event) => {
      const input = event.inputBuffer.getChannelData(0);
      const chunk = new Float32Array(input);
      const maxSamples = Math.round(sampleRateRef.current * (AUDIO_BUFFER_MS / 1000));

      audioBufferRef.current.push(chunk);
      audioBufferSamplesRef.current += chunk.length;

      if (audioBufferSamplesRef.current > maxSamples) {
        const trimmed = trimAudioBufferToLastSamples(audioBufferRef.current, maxSamples);
        audioBufferRef.current = trimmed.chunks;
        audioBufferSamplesRef.current = trimmed.samplesCount;
      }
    };

    source.connect(processor);
    processor.connect(audioContext.destination);

    streamRef.current = stream;
    audioContextRef.current = audioContext;
    sourceRef.current = source;
    processorRef.current = processor;
    intervalRef.current = window.setInterval(() => {
      void flushAudioChunk();
    }, AUDIO_SEND_INTERVAL_MS);
  };

  const start = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Браузер не поддерживает запись с микрофона');
      return;
    }

    setLoading(true);
    setError(null);
    setElapsed(0);
    setLiveDbfs(null);
    setProcessedChunks(0);
    setIncludedChunks(0);
    setLastResult(null);
    setNoisePoints([]);
    setLessonTimelineJson([]);
    lessonStartedAtRef.current = Date.now();
    timelineEventsRef.current = [];
    audioBufferRef.current = [];
    audioBufferSamplesRef.current = 0;

    try {
      await startMicrophone();
      setPhase('recording');
    } catch (e) {
      await stopMicrophone();
      setError(e instanceof Error ? e.message : 'Не удалось включить микрофон');
    } finally {
      setLoading(false);
    }
  };

  const stop = async () => {
    setLoading(true);
    setError(null);

    try {
      await stopMicrophone();
      setLessonTimelineJson(buildTimelineJson(timelineEventsRef.current, lessonStartedAtRef.current));
      setPhase('report');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось завершить анализ');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setElapsed(0);
    setLiveDbfs(null);
    setProcessedChunks(0);
    setIncludedChunks(0);
    setLastResult(null);
    setNoisePoints([]);
    setLessonTimelineJson([]);
    lessonStartedAtRef.current = null;
    timelineEventsRef.current = [];
    audioBufferRef.current = [];
    audioBufferSamplesRef.current = 0;
    setError(null);
    setPhase('idle');
  };

  useEffect(() => {
    return () => {
      void stopMicrophone();
    };
  }, []);

  return (
    <div className="page" data-timeline-windows={lessonTimelineJson.length}>
      <PageHeader
        title="Анализ урока"
        description="Запись шума и итоговая статистика урока"
        actions={
          phase === 'recording' ? (
            <button type="button" className="btn btn--danger" disabled={loading} onClick={() => void stop()}>
              {loading ? '…' : 'Завершить урок'}
            </button>
          ) : phase === 'report' ? (
            <button type="button" className="btn" onClick={reset}>
              Новый урок
            </button>
          ) : (
            <button type="button" className="btn btn--primary" disabled={loading} onClick={() => void start()}>
              {loading ? '…' : 'Начать урок'}
            </button>
          )
        }
      />

      {error && <div className="auth-alert">{error}</div>}

      {/* ─── ОЖИДАНИЕ ─── */}
      {phase === 'idle' && (
        <PlaceholderCard title="Запись не активна">
          <p className="muted">
            Нажмите «Начать урок» — система включит микрофон, будет хранить последние 5 секунд аудио
            и отправлять это окно на анализ каждую секунду и в конце покажет статистику шума.
          </p>
        </PlaceholderCard>
      )}

      {/* ─── ЗАПИСЬ ─── */}
      {phase === 'recording' && (
        <div className="form-grid">
          <PlaceholderCard title="Уровень шума сейчас">
            <LiveIndicator dbfs={liveDbfs} />
          </PlaceholderCard>

          <PlaceholderCard title="Идёт запись урока">
            <p className="recording-indicator recording-indicator--active">
              🔴 Запись · {formatDuration(elapsed)}
            </p>
            <p className="muted">
              Алиса хранит последние 5 секунд аудио и каждую секунду отправляет это окно на анализ.
              В статистику попадут только отрезки, когда учитель не говорит.
            </p>
            <p className="muted">
              Обработано отрезков: {processedChunks}. В статистике: {includedChunks}.
            </p>
            {lastResult && (
              <p className="muted">
                Последнее состояние: {humanNoiseStatus(lastResult)}; уровень:{' '}
                {lastResult.current_dbfs.toFixed(1)} dBFS
              </p>
            )}
          </PlaceholderCard>
        </div>
      )}

      {/* ─── ОТЧЁТ ─── */}
      {phase === 'report' && (
        <>
          <div className="stats-row">
            <StatCard
              value={avgNoise === null ? '—' : Number(avgNoise.toFixed(1))}
              label="Средний уровень"
              unit="dBFS"
            />
            <StatCard
              value={peakNoise === null ? '—' : Number(peakNoise.toFixed(1))}
              label="Пиковый уровень"
              unit="dBFS"
            />
            <StatCard value={loudChunks} label="Шумных отрезков" unit="" />
          </div>

          <PlaceholderCard title="Итог анализа шума">
            {noisePoints.length ? (
              <ul className="bullet-list">
                <li>Длительность записи: {formatDuration(elapsed)}.</li>
                <li>Всего обработано аудио-отрезков: {processedChunks}.</li>
                <li>В расчёт статистики включено отрезков: {includedChunks}.</li>
                <li>
                  Самый высокий зафиксированный уровень:{' '}
                  {peakNoise === null ? '—' : `${peakNoise.toFixed(1)} dBFS`}.
                </li>
                <li>
                  Средний уровень по включённым отрезкам:{' '}
                  {avgNoise === null ? '—' : `${avgNoise.toFixed(1)} dBFS`}.
                </li>
              </ul>
            ) : (
              <p className="muted">
                Для отчёта нет подходящих точек: все полученные отрезки были исключены из
                статистики или запись была слишком короткой.
              </p>
            )}
          </PlaceholderCard>

          <PlaceholderCard title="График шума">
            <NoiseChart points={noisePoints} />
            <div className="noise-legend">
              <span><i className="dot dot--quiet" /> тихо (&lt; -45 dBFS)</span>
              <span><i className="dot dot--normal" /> рабочий шум (-45…-30 dBFS)</span>
              <span><i className="dot dot--loud" /> шумно (&gt; -30 dBFS)</span>
            </div>
            <p className="muted">
              На графике показан только шум, когда учитель не говорит.
            </p>
          </PlaceholderCard>
        </>
      )}
    </div>
  );
}
