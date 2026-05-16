# Помощник учителя — Backend

API на **FastAPI** с **PostgreSQL** (расписания, оценки, пользователи) и **MinIO** (фото домашних работ, аудио уроков).

## Стек

- FastAPI + Uvicorn
- SQLAlchemy 2 + PostgreSQL
- JWT (python-jose) + bcrypt (passlib)
- MinIO (S3-совместимое хранилище)

## Быстрый старт

### 1. Инфраструктура

```bash
cd backend
docker compose up -d
cp .env.example .env
```

### 2. Python-окружение

Требуется **Python 3.9+** (рекомендуется 3.11+).

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Запуск API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- MinIO Console: http://localhost:9001 (логин `minio` / `minio123`)

При старте создаются таблицы, бакеты MinIO и демо-пользователи.

## Демо-аккаунты

| Email | Пароль | Роль |
|-------|--------|------|
| `director@school.ru` | `director123` | Директор |
| `teacher@school.ru` | `teacher123` | Учитель |
| `student@school.ru` | `student123` | Ученик |

## Авторизация (JWT)

```http
POST /api/auth/register
Content-Type: application/json

{
  "name": "Иванов И.И.",
  "email": "user@school.ru",
  "password": "secret12",
  "role": "student"
}
```

```http
POST /api/auth/login
Content-Type: application/json

{ "email": "teacher@school.ru", "password": "teacher123" }
```

Ответ:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": { "id": "...", "name": "...", "email": "...", "role": "teacher" }
}
```

Дальнейшие запросы: `Authorization: Bearer <jwt>`

## Основные эндпоинты

| Метод | Путь | Роль | Описание |
|-------|------|------|----------|
| GET | `/api/auth/me` | * | Текущий пользователь |
| GET | `/api/schedule/me` | teacher, student | Моё расписание |
| GET | `/api/schedule/user/{id}` | director | Расписание пользователя |
| POST | `/api/schedule/generate` | director | Генерация расписания |
| GET | `/api/homework/teacher` | teacher | Работы на проверку |
| POST | `/api/homework/upload` | student | Загрузка фото (multipart) |
| PATCH | `/api/homework/{id}/grade` | teacher | Подтверждение оценки |
| POST | `/api/noise/sessions` | teacher | Старт анализа шума |
| POST | `/api/noise/sessions/{id}/stop` | teacher | Стоп + аудио (опционально) |
| GET | `/api/noise/lessons` | teacher, director | Список уроков |
| GET | `/api/classes` | director, teacher | Классы |
| PUT | `/api/classes/{id}/teacher` | director | Назначить учителя |
| GET | `/api/stats/teacher` | teacher | Сводка |
| GET | `/api/stats/class/{id}/grades` | teacher, director | Оценки класса |

## Структура

```
backend/
├── app/
│   ├── main.py           # Точка входа FastAPI
│   ├── config.py         # Настройки из .env
│   ├── database.py
│   ├── dependencies.py   # JWT, роли
│   ├── models/           # SQLAlchemy
│   ├── schemas/          # Pydantic
│   ├── api/routes/       # Роутеры
│   ├── services/         # MinIO, генератор расписания, ИИ-заглушки
│   └── seed.py           # Демо-данные
├── docker-compose.yml
└── requirements.txt
```

## MinIO

- Бакет `homework` — фотографии домашних работ
- Бакет `lesson-media` — аудио/видео уроков

Клиенту отдаются presigned URL (временные ссылки на скачивание).

## Переменные окружения

См. `.env.example`.
