# База знаний для Yandex AI Search

Готовые чанки из `app/data/subject_knowledge.py` — **по одной строке JSON на каждый учебный факт**.

## Какой файл загружать

| Файл | Когда использовать |
|------|-------------------|
| **`knowledge_prechunked.jsonl`** | Консоль AI Studio: «Индекс на основе **вашего** разбиения» → файл с чанками в формате **JSON Line** |
| `knowledge_chunks.jsonl` | Отладка, внутренние скрипты (поле `text` вместо `content`) |

## Формат для консоли (`knowledge_prechunked.jsonl`)

Каждая **строка** — один готовый чанк (Yandex не режет файл сам):

```json
{
  "content": "Предмет: Математика. Тема: Дроби. Класс: 5-6.\n\nЧтобы сложить дроби с разными знаменателями...",
  "metadata": {
    "subject": "Математика",
    "topic": "Дроби",
    "grade_from": 5,
    "grade_to": 6,
    "grade_label": "5-6",
    "sort_order": 20,
    "chunk_id": "k_848686b270ec",
    "source": "subject_knowledge"
  }
}
```

- **content** — текст чанка для индекса (не длиннее 8000 символов).
- **metadata** — атрибуты для фильтрации (опционально, но полезно).

Расширение файла: `.jsonl` или `.jsonlines`. Кодировка: **UTF-8**.

## Пересобрать после правок фактов

```bash
cd backend
.venv/bin/python ai_search/build_knowledge_jsonl.py
```

## Создать индекс в AI Studio (рекомендуется)

1. [Консоль Yandex Cloud](https://console.yandex.cloud/) → каталог `YANDEX_FOLDER_ID`.
2. **AI Studio** → **Поисковые индексы** (Vector store) → **Создать**.
3. Выберите режим вроде **«На основе вашего разбиения»** / pre-chunked.
4. Загрузите файл **`knowledge_prechunked.jsonl`**.
5. Дождитесь статуса `completed`, скопируйте **ID индекса** в `.env`:

```env
YANDEX_KNOWLEDGE_INDEX_ID=fvt...
KNOWLEDGE_SEARCH_MODE=ai_search
```

6. Перезапустите бэкенд.

## Проверка

Загрузите домашку → в `ai_comment` должно быть: `База знаний: ai_search`.
