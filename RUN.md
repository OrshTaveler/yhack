# Запуск проекта — полная инструкция

Приложение состоит из **4 компонентов**, которые запускаются отдельно:

| # | Компонент | Порт | Назначение |
|---|-----------|------|-----------|
| 1 | Docker (PostgreSQL + MinIO) | 5433 / 9000-9001 | БД и хранилище файлов |
| 2 | Backend API | 8000 | Основное API приложения |
| 3 | alice_mcp (голосовой сервис) | 8001 | Анализ урока: шум, диктор, расшифровка |
| 4 | Frontend | 5173 | Веб-интерфейс |

---

## Требования

- **Docker Desktop**
- **Python 3.12**
- **Node.js 18+**

---

## Шаг 0. Переменные окружения

Создай файл `backend/.env` (скопируй из `backend/.env.example`) и заполни ключи:

```env
# PostgreSQL
DATABASE_URL=postgresql+psycopg2://teacher:teacher@127.0.0.1:5433/teacher_assistant

# JWT
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=minio123
MINIO_SECURE=false
MINIO_BUCKET_HOMEWORK=homework
MINIO_BUCKET_LESSON_MEDIA=lesson-media

# App
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
API_PREFIX=/api

# Yandex AI Studio (OCR, YandexGPT, AI Search)
YANDEX_API_KEY=<ключ из AI Studio>
YANDEX_FOLDER_ID=<b1g...>
YANDEX_KNOWLEDGE_INDEX_ID=<id индекса базы знаний>

# text.ru — антиплагиат
TEXTRU_USERKEY=<userkey с text.ru>
```

> `alice_mcp` ключи **не нужны** — он работает на локальных моделях (Whisper, SpeechBrain).

---

## Шаг 1. Docker — БД и хранилище

```bash
cd backend
docker compose up -d
```

Проверка: `docker ps` — должны быть контейнеры `db` и `minio`.

---

## Шаг 2. Backend API (порт 8000)

```bash
cd backend

# создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
python run.py
```

Готово, когда в консоли: `Application startup complete`.
Проверка: открыть http://localhost:8000/docs

---

## Шаг 3. alice_mcp — голосовой сервис (порт 8001)

Отдельное окружение (тяжёлые ML-зависимости: torch, speechbrain, faster-whisper).

```bash
cd alice_mcp

python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
python api.py
```

> **Первый запуск долгий** — скачиваются модели SpeechBrain (~80 МБ) и
> Whisper base (~140 МБ). Готово, когда: `Uvicorn running on http://0.0.0.0:8001`.

Проверка: http://localhost:8001/health → `{"status":"ok"}`

В консоли должно быть:
- `VoiceDetector: модель распознавания диктора загружена.`
- `VoiceTranscriber: модель Whisper «base» загружена.`

---

## Шаг 4. Frontend (порт 5173)

```bash
cd frontend
npm install
npm run dev
```

Открыть: **http://localhost:5173**

---

## Демо-аккаунты

| Роль | Email | Пароль |
|------|-------|--------|
| Учитель | `teacher@school.ru` | `teacher123` |
| Ученик | `student@school.ru` | `student123` |

Создаются автоматически при первом старте backend.

---

## Порядок запуска

```
1. docker compose up -d   (БД должна быть первой)
2. backend  (python run.py)
3. alice_mcp (python api.py)
4. frontend (npm run dev)
```

---

## Что где проверить

| Модуль | Где | Как |
|--------|-----|-----|
| Проверка ДЗ | Ученик → «Домашние задания» | Загрузить фото → OCR + антиплагиат + AI-проверка |
| Профиль ученика | Ученик → «Мой профиль» | Прогресс, слабые темы |
| Анализ урока | Учитель → «Анализ урока» | «Начать урок» → говорить → «Завершить» |
| Проверка работ | Учитель → «Проверка работ» | Список работ учеников |

---

## Возможные проблемы

| Симптом | Решение |
|---------|---------|
| Backend: ошибка подключения к БД | Docker не запущен — `docker compose up -d` |
| alice_mcp: `VoiceDetector ... режим «только шум»` | На Windows — модель диктора не грузится (симлинки). На macOS грузится нормально |
| Порт 5173 занят | Vite сам возьмёт 5174/5175 — смотри адрес в консоли |
| Схема БД устарела (ошибки колонок) | Пересоздать БД: `docker compose down -v && docker compose up -d` |
| Микрофон не пишет | Разрешить доступ к микрофону в браузере |

---

## Архитектура сервисов

```
Frontend (5173)
   ├── /api/*           → Backend (8000) → PostgreSQL + MinIO + Yandex AI Studio
   └── :8001/*          → alice_mcp (8001) — шум, диктор, расшифровка речи

Модуль анализа урока:
   фронт пишет аудио → alice_mcp (8001):
       /recognize-voice  — живой анализ чанка (шум + говорит ли учитель)
       /transcribe       — расшифровка всего урока в конце
   → Backend /api/lesson/analyze — YandexGPT формирует отчёт
       (упоминания учеников, тезисы урока, домашнее задание)
```
