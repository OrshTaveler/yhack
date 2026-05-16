# Архитектура модуля «Ученик» — проверка ДЗ по базе знаний

> Модуль: загрузка ДЗ → OCR → антиплагиат → проверка по базе знаний → профиль ученика
> Стек: FastAPI · MinIO · Yandex AI Studio (Vision OCR, AI Search, YandexGPT) · ZeroGPT

---

## 1. Полный поток (pipeline)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Ученик грузит фото ДЗ        [HomeworkUploadPage] ✅ есть │
│     POST /homework/upload  (multipart: subject_id, file)      │
└────────────────────────────┬──────────────────────────────────┘
                             │  файл → MinIO, запись в БД (status=pending)
                             │  ответ ученику СРАЗУ (не ждём проверку)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  ФОНОВАЯ ЗАДАЧА (BackgroundTask) — пайплайн проверки           │
│                                                               │
│  2. Vision OCR        фото → печатный текст                   │
│         ↓                                                     │
│  3. ZeroGPT           текст → % AI-генерации (антисписывание)  │
│         ↓                                                     │
│  4. AI Search         поиск эталона/темы в базе знаний        │
│         ↓                                                     │
│  5. YandexGPT         сравнение работы с эталоном →           │
│                       оценка + ошибки + 3 наводящих вопроса   │
│         ↓                                                     │
│  6. Запись в БД       status=ai_reviewed, всё сохранено       │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend опрашивает GET /homework/my каждые 3 сек            │
│  Видит status=ai_reviewed → показывает результат              │
│  Данные попадают в профиль  [StudentProfilePage] ✅ есть      │
└─────────────────────────────────────────────────────────────┘
```

**Ключевое архитектурное решение:** проверка идёт в **фоне**, а не внутри запроса
загрузки. 4 внешних API (OCR + ZeroGPT + Search + GPT) = 10–20 сек. Заставлять
ученика ждать ответа HTTP всё это время — плохо. Поэтому:
- `upload` сохраняет файл и возвращает ответ мгновенно (`status=pending`)
- пайплайн крутится в `BackgroundTask`
- фронт опрашивает список и показывает результат когда `status=ai_reviewed`

---

## 2. Компоненты (сервисы backend)

| Файл | Ответственность |
|------|-----------------|
| `services/storage.py` | MinIO — загрузка/выдача файла ✅ есть |
| `services/ocr.py` | **новый** — Yandex Vision OCR: фото → текст |
| `services/plagiarism.py` | **новый** — ZeroGPT: текст → % AI |
| `services/knowledge_base.py` | **новый** — AI Search: поиск эталона по теме |
| `services/homework_ai.py` | **переписать** — оркестратор пайплайна + YandexGPT |
| `services/yandex_gpt.py` | **новый** — низкоуровневый клиент YandexGPT |

Каждый сервис изолирован и имеет **fallback-заглушку** — если внешний API
недоступен (нет ключа / лимит / сеть), возвращает разумный мок, демо не падает.

---

## 3. Модель данных — изменения

### `HomeworkSubmission` (добавить поля)

```python
# OCR
ocr_text: Mapped[str | None]              # распознанный печатный текст

# Антиплагиат (ZeroGPT)
ai_text_probability: Mapped[float | None] # 0..100, % вероятности AI
plagiarism_flag: Mapped[str | None]       # "clean" | "suspicious" | "high"

# Результат проверки (YandexGPT)
ai_grade: Mapped[float | None]            # ✅ уже есть
ai_comment: Mapped[str | None]            # ✅ уже есть — краткий вывод
ai_errors: Mapped[str | None]             # JSON-список конкретных ошибок
ai_questions: Mapped[str | None]          # JSON-список 3 наводящих вопросов

# Контекст проверки
checked_topic: Mapped[str | None]         # тема, по которой сверяли
status: Mapped[HomeworkStatus]            # ✅ есть: pending→ai_reviewed→teacher_reviewed
```

> `ai_errors` и `ai_questions` храним как JSON-строку (`Text`) — без отдельных
> таблиц, для хакатона достаточно. Парсятся на фронте.

### База знаний — новая таблица `KnowledgeDocument`

```python
class KnowledgeDocument:
    id: UUID
    subject_id: UUID            # к какому предмету
    topic: str                  # название темы
    content: Text               # текст эталона / материала
    uploaded_by: UUID           # учитель, который загрузил
```

> Вариант А (проще): эталон берётся прямо из этой таблицы по теме.
> Вариант Б (RAG): документы индексируются в **Yandex AI Search**, поиск семантический.

---

## 4. API-эндпоинты

| Метод | Путь | Роль | Назначение |
|-------|------|------|-----------|
| POST | `/homework/upload` | student | Загрузка ДЗ ✅ есть (доработать: фон) |
| GET | `/homework/my` | student | Список работ + статус ✅ есть |
| GET | `/homework/{id}` | student/teacher | **новый** — детали одной работы |
| POST | `/knowledge/upload` | teacher | **новый** — учитель грузит эталон/материал |
| GET | `/knowledge?subject_id=` | teacher | **новый** — список материалов |
| GET | `/profile/me` | student | Профиль ✅ есть |

---

## 5. Детализация пайплайна (фоновая задача)

```python
# services/homework_ai.py — оркестратор

async def run_homework_pipeline(submission_id: UUID):
    db = SessionLocal()
    sub = db.get(HomeworkSubmission, submission_id)

    # ── Шаг 2: OCR ───────────────────────────────
    image_bytes = download_from_minio(sub.file_key)
    sub.ocr_text = await ocr.recognize(image_bytes)        # Vision OCR

    # ── Шаг 3: антиплагиат ───────────────────────
    prob = await plagiarism.check_ai_generated(sub.ocr_text)  # ZeroGPT
    sub.ai_text_probability = prob
    sub.plagiarism_flag = (
        "high" if prob > 70 else
        "suspicious" if prob > 30 else "clean"
    )

    # ── Шаг 4: база знаний ───────────────────────
    reference = await knowledge_base.find_reference(       # AI Search
        subject_id=sub.subject_id, query=sub.ocr_text
    )
    sub.checked_topic = reference.topic

    # ── Шаг 5: проверка YandexGPT ────────────────
    result = await yandex_gpt.review_homework(
        student_text=sub.ocr_text,
        reference=reference.content,
    )
    sub.ai_grade     = result.grade
    sub.ai_comment   = result.summary
    sub.ai_errors    = json.dumps(result.errors, ensure_ascii=False)
    sub.ai_questions = json.dumps(result.questions, ensure_ascii=False)

    # ── Шаг 6: финализация ───────────────────────
    sub.status = HomeworkStatus.ai_reviewed
    db.commit()
```

### Промпт для YandexGPT (шаг 5)

```
Ты школьный учитель. Проверь работу ученика, сравнив её с эталоном.

ЭТАЛОН (из базы знаний):
{reference}

РАБОТА УЧЕНИКА:
{student_text}

Верни строго JSON:
{
  "grade": 4.0,                       // оценка 2–5
  "summary": "краткий вывод",
  "errors": ["ошибка 1", "ошибка 2"], // конкретные ошибки
  "questions": [                      // 3 НАВОДЯЩИХ вопроса,
    "...", "...", "..."               // НЕ давать готовый ответ
  ]
}
```

---

## 6. Обработка ошибок и fallback

Каждый внешний вызов обёрнут так:

```python
async def recognize(image_bytes) -> str:
    try:
        if not settings.yandex_vision_api_key:
            return _MOCK_OCR_TEXT          # ключа нет → заглушка
        return await _call_vision(image_bytes)
    except Exception:
        logger.warning("OCR failed, using fallback")
        return _MOCK_OCR_TEXT              # API упал → заглушка
```

Принцип: **демо никогда не падает**. Нет ключа или API лёг — пайплайн идёт
дальше на моках. Это важно для презентации.

Если весь пайплайн упал — `status` остаётся `pending`, фронт показывает
«проверка не удалась, попробуйте позже».

---

## 7. Frontend — изменения

| Страница | Что добавить |
|----------|-------------|
| `HomeworkUploadPage` ✅ | После загрузки — индикатор «🔄 Идёт проверка…», опрос статуса |
| `StudentProfilePage` ✅ | В блоке работ: флаг плагиата, ошибки, наводящие вопросы |
| `HomeworkDetailPage` | **новая** — полная карточка: OCR-текст, оценка, ошибки, вопросы, % AI |

### Отображение флага плагиата

```
clean       → ✅ Написано самостоятельно
suspicious  → 🟡 Возможны заимствования (30–70%)
high        → 🔴 Высокая вероятность AI (>70%) — отправлено учителю
```

---

## 8. Структура новых файлов

```
backend/app/
├── services/
│   ├── ocr.py                  ← Vision OCR + fallback
│   ├── plagiarism.py           ← ZeroGPT + fallback
│   ├── knowledge_base.py       ← AI Search + fallback
│   ├── yandex_gpt.py           ← клиент YandexGPT
│   └── homework_ai.py          ← оркестратор (переписать)
├── models/
│   ├── homework.py             ← + новые поля
│   └── knowledge.py            ← новая таблица KnowledgeDocument
├── schemas/
│   ├── homework.py             ← + ocr_text, errors, questions, plagiarism
│   └── knowledge.py            ← новая
└── api/routes/
    ├── homework.py             ← + GET /{id}, фон-задача
    └── knowledge.py            ← новый роут

frontend/src/
├── pages/student/
│   └── HomeworkDetailPage.tsx  ← новая
└── api/types.ts                ← + поля
```

---

## 9. Порядок реализации (для хакатона)

| # | Шаг | Время | Зависимость |
|---|-----|-------|-------------|
| 1 | Поля в модели + миграция БД | 30 мин | — |
| 2 | `ocr.py` с fallback-заглушкой | 30 мин | — |
| 3 | `plagiarism.py` (ZeroGPT) с fallback | 40 мин | — |
| 4 | `yandex_gpt.py` + `homework_ai.py` оркестратор | 1.5 ч | 1,2 |
| 5 | Фоновая задача в `upload` + опрос на фронте | 1 ч | 4 |
| 6 | `knowledge_base.py` (вариант А — из БД) | 1 ч | 1 |
| 7 | UI: флаги, ошибки, вопросы в профиле | 1 ч | 5 |
| 8 | (опц.) Вариант Б — реальный AI Search | +2 ч | 6 |

**MVP-минимум для демо:** шаги 1–5 + 7. База знаний — вариант А (эталон из БД
или хардкод). Это уже полный рабочий сценарий с реальным YandexGPT и ZeroGPT.

---

## 10. Какие критерии хакатона закрывает модуль

| Критерий | Чем закрыт |
|----------|-----------|
| Обработка изображений / файлов | Фото ДЗ → MinIO |
| OCR | Vision OCR: рукопись → печатный текст |
| RAG / база знаний | AI Search по эталонам и учебникам |
| Внешние API | ZeroGPT (антиплагиат) |
| Текстовая генерация | YandexGPT: ошибки + наводящие вопросы |
| Агентный сценарий | Цепочка OCR → антиплагиат → поиск → анализ |
| Хранение прогресса | Результаты пишутся в профиль ученика |
| Структурирование результата | JSON-отчёт: оценка + ошибки + вопросы |
