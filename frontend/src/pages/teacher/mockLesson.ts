/**
 * МОК-данные анализа урока.
 * Когда напарник доделает модуль (SpeechKit + YandexGPT) — заменить
 * импорт этих констант на ответ от API /noise/sessions/{id}/report.
 *
 * Структура специально совпадает с тем, что вернёт реальный бэкенд:
 *   noiseSamples   ← SpeechKit + амплитуда
 *   students       ← YandexGPT (разбор «Иванов, молодец»)
 *   summary        ← YandexGPT (тезисы урока)
 *   homework       ← YandexGPT (по ключевым словам «задание», «на дом»)
 */

export type BehaviorStatus = 'active' | 'normal' | 'distracted' | 'noisy';

export interface StudentBehavior {
  name: string;
  status: BehaviorStatus;
  note: string; // что именно сказал учитель / как себя вёл
}

export interface NoiseSample {
  minute: number;
  level_db: number;
}

/** Уровень шума поминутно за урок (38 минут). */
export const MOCK_NOISE: NoiseSample[] = [
  42, 45, 44, 48, 52, 50, 47, 46, 55, 62,
  68, 71, 65, 58, 54, 50, 48, 47, 49, 52,
  56, 60, 64, 70, 73, 67, 59, 53, 50, 48,
  46, 49, 55, 61, 58, 52, 47, 44,
].map((level_db, i) => ({ minute: i + 1, level_db }));

/** Поведение учеников — собрано из реплик учителя. */
export const MOCK_STUDENTS: StudentBehavior[] = [
  { name: 'Иванов Пётр', status: 'active', note: '«Иванов, молодец» — активно отвечал у доски' },
  { name: 'Петрова Анна', status: 'active', note: '«Аня, отлично» — верно решила задачу' },
  { name: 'Смирнова Ольга', status: 'normal', note: 'Работала спокойно, без замечаний' },
  { name: 'Кузнецов Илья', status: 'distracted', note: '«Кузнецов, не отвлекайся» — 1 замечание' },
  { name: 'Сидоров Максим', status: 'noisy', note: '«Сидоров, потише» — 2 замечания за урок' },
];

/** Тезисы урока — что было. */
export const MOCK_SUMMARY: string[] = [
  'Тема урока: «Фотосинтез и дыхание растений»',
  'Повторили строение листа и роль хлорофилла',
  'Разобрали опыт с водным растением и выделением кислорода',
  'Класс активно участвовал в обсуждении первые 20 минут',
  'На 23–25 минутах — всплеск шума, потребовалось замечание',
];

/** Домашнее задание — выделено по ключевым словам. */
export const MOCK_HOMEWORK =
  '§14, упражнения 3–5 на стр. 67. Подготовить короткое сообщение о значении фотосинтеза.';
