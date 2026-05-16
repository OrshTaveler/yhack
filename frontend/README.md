# Помощник учителя — Frontend

Веб-интерфейс школьной платформы **«Помощник учителя»**: анализ шума на уроках, генерация расписания, проверка домашних работ с помощью ИИ.

Стек: **React 19**, **TypeScript**, **Vite**, **React Router 7**.

## Быстрый старт

```bash
cd frontend
npm install
npm run dev
```

Приложение откроется на [http://localhost:5173](http://localhost:5173). Запросы к API проксируются на `http://localhost:8000` (см. `vite.config.ts`).

Сборка для продакшена:

```bash
npm run build
npm run preview
```

Переменная окружения (опционально):

```env
VITE_API_URL=/api
```

## Роли и возможности

| Роль | Возможности |
|------|-------------|
| **Директор** | Генерация расписания из списка классов, предметов и часов в неделю; назначение классов преподавателям; просмотр расписания любого учителя/ученика; статистика урока (шум, выжимка) |
| **Учитель** | Проверка домашних работ (оценка ИИ, фото, правка оценки, доп. вопросы); анализ шума в классе с отчётом в конце урока; статистика по своим классам, оценкам и работам учеников; расписание |
| **Ученик** | Загрузка фото домашней работы (после проверки ИИ работа видна учителю); просмотр оценок; расписание |

> Авторизация через **JWT** бэкенда (`POST /api/auth/login`, `/api/auth/register`). Токен хранится в `localStorage`.

Запустите бэкенд (`cd backend && docker compose up -d && uvicorn app.main:app --reload`) и инфраструктуру перед входом.

### Демо-аккаунты (создаются при старте бэкенда)

| Email | Пароль | Роль |
|-------|--------|------|
| `director@school.ru` | `director123` | Директор |
| `teacher@school.ru` | `teacher123` | Учитель |
| `student@school.ru` | `student123` | Ученик |

## Маршруты

### Общие

| Путь | Кто | Описание |
|------|-----|----------|
| `/login` | все | Вход по email и паролю |
| `/register` | все | Регистрация нового пользователя |
| `/schedule` | учитель, ученик | Личное расписание |

### Директор (`/director/*`)

| Путь | Описание |
|------|----------|
| `/director` | Обзор |
| `/director/schedule-generator` | Генерация расписания |
| `/director/assignments` | Назначение классов учителям |
| `/director/schedules` | Расписание выбранного пользователя |
| `/director/lesson-stats` | Статистика уроков (шум, выжимка) |

### Учитель (`/teacher/*`)

| Путь | Описание |
|------|----------|
| `/teacher` | Обзор |
| `/teacher/homework` | Очередь работ с оценкой ИИ и фото |
| `/teacher/noise` | Запись и анализ шума на уроке |
| `/teacher/statistics` | Статистика по классам и ученикам |

### Ученик (`/student/*`)

| Путь | Описание |
|------|----------|
| `/student` | Обзор |
| `/student/homework` | Загрузка фото домашки |
| `/student/grades` | История оценок |

Доступ к маршрутам ограничен по роли (`RoleGuard`, `RequireAuth`).

## Структура проекта

```
frontend/
├── src/
│   ├── api/client.ts          # HTTP-клиент к бэкенду
│   ├── components/
│   │   ├── common/            # PageHeader, RoleGuard, PlaceholderCard
│   │   └── layout/            # AppLayout, Sidebar
│   ├── contexts/AuthContext.tsx
│   ├── hooks/useAuth.ts
│   ├── pages/
│   │   ├── director/          # Экраны директора
│   │   ├── teacher/           # Экраны учителя
│   │   ├── student/           # Экраны ученика
│   │   └── shared/            # Расписание
│   ├── routes/index.tsx       # Маршрутизация
│   └── types/index.ts         # Доменные типы
├── package.json
└── vite.config.ts
```

## Интеграция с бэкендом

Заготовки эндпоинтов в `src/api/client.ts`:

- `POST /api/auth/login` — авторизация
- `GET /api/schedule/me`, `GET /api/schedule/user/:id`, `POST /api/schedule/generate`
- `GET /api/homework/teacher`, `POST /api/homework/upload`, `PATCH /api/homework/:id/grade`
- `POST /api/noise/sessions`, отчёты и статистика уроков
- `GET /api/classes`, назначение учителя на класс
- `GET /api/stats/teacher`, оценки по классу

Типы сущностей: `User`, `HomeworkSubmission`, `LessonNoiseReport`, `ScheduleSlot` и др. — в `src/types/index.ts`.

## Дальнейшие шаги

1. Подключить остальные экраны к API (расписание, домашки, шум).
2. Реализовать загрузку данных на страницах через `api.*`.
3. Добавить графики (например, Recharts) для шума и статистики.
4. WebSocket или polling для live-уровня шума на уроке.
