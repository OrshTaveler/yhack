# Модуль проверки домашних работ — документация

> Статус: **реализовано и проверено e2e**
> Модуль: ученик загружает фото ДЗ → OCR → антиплагиат → AI-детектор → результат в профиль
> Стек: FastAPI · MinIO · Yandex Vision OCR · YandexGPT · text.ru

---

## 1. Что работает сейчас

```
Ученик грузит фото ДЗ
      ↓  POST /homework/upload  → ответ СРАЗУ (status=pending)
      ↓
ФОНОВАЯ ЗАДАЧА (BackgroundTasks):
   1. Vision OCR   — фото (рукопись) → печатный текст
   2. text.ru      — % уникальности + источники списывания
   3. YandexGPT    — % вероятности AI-генерации + причина
      ↓
   status=ai_reviewed, результаты в БД
      ↓
Фронт опрашивает GET /homework/my каждые 5 сек → показывает результат
```

Проверено e2e: загрузка рукописного фото → через ~35 сек готов отчёт.

---

## 2. Структура файлов

```
backend/app/
├── services/
│   ├── ocr.py              # Vision OCR (модель "handwritten") + fallback
│   ├── plagiarism.py       # text.ru, двухшаговый API + fallback
│   ├── ai_detector.py      # YandexGPT-детектор AI-текста + fallback
│   ├── homework_ai.py      # ОРКЕСТРАТОР пайплайна (run_homework_pipeline)
│   └── storage.py          # MinIO: upload_file, download_file, presigned_url
├── models/homework.py      # HomeworkSubmission + поля результатов
├── schemas/homework.py     # HomeworkOut + PlagiarismSource
└── api/routes/homework.py  # upload (фон), list, grade

backend/scripts/            # standalone-тесты (не часть приложения)
├── test_ocr.py             # проверка только OCR
├── test_textru.py          # проверка только text.ru
├── test_gpt_detector.py    # проверка только AI-детектора
├── test_pipeline.py        # OCR → text.ru без приложения
└── test_e2e_upload.py      # полный тест через API приложения

frontend/src/
├── pages/student/HomeworkUploadPage.tsx  # загрузка + показ результата + опрос
└── api/types.ts                          # HomeworkDto + PlagiarismSourceDto
```

---

## 3. Модель данных — `HomeworkSubmission`

| Поле | Тип | Кто заполняет | Описание |
|------|-----|---------------|----------|
| `file_key` | str | upload | ключ файла в MinIO |
| `status` | enum | upload/пайплайн | `pending` → `ai_reviewed` → `teacher_reviewed` |
| `ocr_text` | text | OCR | распознанный текст |
| `text_unique` | float | text.ru | % уникальности (0–100) |
| `plagiarism_sources` | text(JSON) | text.ru | `[{url, plagiat}]` — источники |
| `ai_probability` | float | YandexGPT | % вероятности AI (0–100) |
| `ai_detector_reason` | text | YandexGPT | обоснование вердикта |
| `ai_comment` | text | оркестратор | краткая сводка |
| `ai_grade` | float | — | **пока не заполняется** (см. п.7) |
| `teacher_grade` | float | учитель | финальная оценка |

---

## 4. API-эндпоинты

| Метод | Путь | Роль | Описание |
|-------|------|------|----------|
| POST | `/homework/upload` | student | Загрузка фото. Возвращает работу со `status=pending`, пайплайн уходит в фон |
| GET | `/homework/my` | student | Список своих работ со всеми полями результата |
| GET | `/homework/teacher` | teacher | Работы учеников класса |
| PATCH | `/homework/{id}/grade` | teacher | Подтверждение оценки учителем |

Формат `HomeworkOut` — см. `schemas/homework.py`.

---

## 5. Сервисы — контракты

### `ocr.recognize(image_bytes: bytes, mime="JPEG") -> str`
Фото → текст. Модель `handwritten`. При ошибке/без ключа → текст-заглушка.

### `plagiarism.check(text: str) -> PlagiarismResult`
```python
PlagiarismResult(unique: float, sources: list[dict], ok: bool)
```
`plagiarism.verdict(unique)` → строcovой вердикт.

### `ai_detector.detect(text: str) -> AiDetectionResult`
```python
AiDetectionResult(probability: float, reason: str, ok: bool)
```

### `homework_ai.run_homework_pipeline(submission_id: UUID) -> None`
Оркестратор. Запускается через `BackgroundTasks`. Открывает свою
DB-сессию, гоняет 3 сервиса, пишет результат, ставит `status=ai_reviewed`.

---

## 6. Принцип отказоустойчивости

Каждый сервис имеет **fallback**: нет API-ключа или внешний сервис упал →
возвращается нейтральная заглушка, пайплайн идёт дальше, **демо не падает**.

| Сервис | Fallback при сбое |
|--------|-------------------|
| OCR | текст-заглушка про фотосинтез |
| text.ru | `unique=100, ok=False` |
| AI-детектор | `probability=0, ok=False` |

Весь пайплайн обёрнут в try/except — при фатальной ошибке `status`
остаётся `pending`.

---

## 7. Точка расширения — следующее звено цепочки

Сейчас пайплайн делает OCR + 2 проверки. **Не хватает** проверки работы
по существу: оценка + ошибки + наводящие вопросы по базе знаний.

### Куда встраивать

В `homework_ai.run_homework_pipeline()`, **после шага 3 (AI-детектор)**,
перед финализацией. Псевдокод:

```python
# ── Шаг 4 (НОВЫЙ): проверка по базе знаний ──
from app.services import knowledge_base, homework_grader

reference = knowledge_base.find_reference(sub.subject_id, ocr_text)
review = homework_grader.grade(student_text=ocr_text, reference=reference)

sub.ai_grade     = review.grade            # поле уже есть в модели
sub.ai_errors    = json.dumps(review.errors)     # новое поле — добавить
sub.ai_questions = json.dumps(review.questions)  # новое поле — добавить
```

### Что нужно добавить для этого звена

1. **Поля в `HomeworkSubmission`:** `ai_errors`, `ai_questions` (text/JSON),
   `checked_topic` (str).
2. **Таблица `KnowledgeDocument`** (`subject_id`, `topic`, `content`) —
   эталоны/учебный материал. Или Yandex AI Search.
3. **Сервис `knowledge_base.py`** — поиск эталона по теме.
4. **Сервис `homework_grader.py`** — вызов YandexGPT с промптом проверки
   (модель уже подключена — см. `ai_detector.py` как образец вызова).
5. **Роут `knowledge.py`** — учитель загружает эталоны.
6. **Схема `HomeworkOut`** — добавить `ai_errors`, `ai_questions`.
7. **Фронт** — показ ошибок и наводящих вопросов в карточке работы.

### Промпт для проверки (готов к использованию)

```
SYSTEM: Ты школьный учитель. Проверь работу ученика по эталону.
Верни СТРОГО JSON: {"grade": 2-5, "summary": "...",
"errors": ["..."], "questions": ["3 наводящих вопроса, НЕ давать ответ"]}

USER: ЭТАЛОН: {reference}

РАБОТА УЧЕНИКА: {ocr_text}
```

Вызов YandexGPT — копировать паттерн из `ai_detector.py`
(`GPT_URL`, заголовки, разбор `result.alternatives[0].message.text`).

---

## 8. Конфигурация (`.env`)

```env
YANDEX_API_KEY=<ключ AI Studio>
YANDEX_FOLDER_ID=<b1g...>
TEXTRU_USERKEY=<ключ text.ru>
```

Читаются в `config.py` → `Settings`. Без ключей модуль работает на
заглушках (см. п.6).

---

## 9. Известные ограничения

- **OCR рукописи** — даёт мелкие ошибки распознавания (углекислого →
  «угликнелого»). Смысл сохраняется, для антиплагиата/детекции достаточно.
- **text.ru** ловит копипаст из интернета, **не** ловит оригинальный
  AI-текст. Для AI-генерации — отдельный детектор (YandexGPT).
- **OCR-ошибки занижают AI-детекцию**: распознанный с ошибками текст
  выглядит «человечнее», % AI падает. Честное ограничение пайплайна.
- **text.ru free-tier** — лимит проверок в день.
- Фоновая задача `BackgroundTasks` живёт в процессе сервера — при
  перезапуске недоделанные проверки теряются (для хакатона приемлемо).

---

## 10. Как тестировать

```bash
cd backend
# отдельные компоненты
python scripts/test_ocr.py фото.jpg
python scripts/test_textru.py
python scripts/test_gpt_detector.py
# полный пайплайн без приложения
python scripts/test_pipeline.py фото.jpg
# сквозной тест через API (бэкенд должен быть запущен)
python scripts/test_e2e_upload.py фото.jpg
```
