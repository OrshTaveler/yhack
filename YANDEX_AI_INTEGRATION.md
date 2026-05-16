# Интеграция Yandex AI — План для хакатона

> **Статус:** Приоритет MVP  
> **Время на реализацию:** 4-6 часов  
> **Команда:** 1-2 разработчика

---

## 📋 Что нужно сделать

### 1. **Проверка домашних работ (самое важное!)**

**Файл:** `backend/app/services/homework_ai.py`

**Сейчас:** Рандомная оценка  
**Надо:** Реальный вызов YandexGPT + OCR

**Шаги:**

```python
# 1. Получить файл из MinIO по ссылке
# 2. Если это изображение → Yandex Vision OCR → текст
# 3. Отправить текст в YandexGPT с промптом:
#    "Ты учитель. Проверь эту работу. Выстави оценку 2-5, 
#     укажи ошибки, 3 вопроса для самопроверки"
# 4. Распарсить ответ (оценка, комментарий, вопросы)
# 5. Сохранить в БД
```

**Credentials:** Нужны переменные в `.env`:
```env
YANDEX_GPT_API_KEY=<твой ключ>
YANDEX_FOLDER_ID=<твой folder_id>
YANDEX_VISION_API_KEY=<отдельный ключ для Vision>
```

**Промпт для GPT:**
```
Ты опытный школьный учитель. Тебе нужно проверить письменную работу ученика.

Текст работы:
{OCR_текст_из_фото}

Структура ответа (JSON):
{
  "grade": 4.5,
  "summary": "Хорошая работа, но есть ошибка в третьем примере",
  "errors": [
    "Ошибка в вычислениях на строке 5",
    "Неправильное использование формулы"
  ],
  "questions": [
    "Можешь объяснить почему ты выбрал этот способ решения?",
    "Проверь вычисления во втором примере",
    "Какая тема вызвала у тебя сложность?"
  ]
}
```

---

### 2. **Анализ шума в классе (голос учителя)**

**Файл:** `backend/app/api/routes/noise.py` → `stop_session()`

**Сейчас:** Хардкод текста в отчёте  
**Надо:** Реальный SpeechKit STT + парсинг имён

**Шаги:**

```python
# 1. Взять аудиофайл из MinIO (session.audio_key)
# 2. Отправить в Yandex SpeechKit STT
# 3. Получить транскрипт с временными метками
# 4. Парсить текст через YandexGPT:
#    "Найди все упоминания учителем имён учеников и контекст
#     (похвала / замечание / вопрос)"
# 5. Сохранить упоминания в StudentNoiseStat
# 6. Генерить резюме урока (тезисы + рекомендации)
```

**Промпт для парсинга:**
```
Ты помощник учителя. Проанализируй транскрипт урока.

Транскрипт:
{TRANSCRIPT}

Найди:
1. Все упоминания имён учеников (фамилии, имена)
2. Контекст: похвала ("молодец", "хорошо") или замечание ("тише", "слушай")
3. Главные темы урока
4. Что задали на дом

Ответ JSON:
{
  "mentions": [
    {"name": "Тимофей", "type": "complaint", "quote": "Тимофей, тише!"},
    {"name": "Макс", "type": "praise", "quote": "Макс, отлично решил!"}
  ],
  "lesson_topics": ["Производная", "Применение в физике"],
  "homework": "Упражнения 5.1-5.5",
  "summary": "Продуктивный урок. Класс активно участвовал."
}
```

---

### 3. **Генерация расписания (опционально)**

**Файл:** `backend/app/services/schedule_generator.py`

**Сейчас:** Случайный алгоритм  
**Можно:** Оставить как есть — для хакатона достаточно

**Но если успеешь:**
```python
# Заменить генератор на YandexGPT с function calling:
# "Сгенерируй расписание по этим правилам..."
# Это выглядит красиво в демо
```

---

## 🔧 Технические детали

### Как вызывать Yandex AI

**Все ключи в одну переменную + Folder ID:**

```python
from app.config import get_settings

settings = get_settings()
api_key = settings.yandex_gpt_api_key
folder_id = settings.yandex_folder_id
```

**YandexGPT (через REST API):**

```python
import httpx

async def call_gpt(prompt: str) -> str:
    """Вызов YandexGPT через REST API"""
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "user",
                "text": prompt
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "x-folder-id": folder_id
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        result = response.json()
        return result["result"]["alternatives"][0]["message"]["text"]
```

**Yandex SpeechKit STT:**

```python
import httpx

async def transcribe_audio(audio_path: str) -> str:
    """Транскрипция аудио"""
    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    
    with open(audio_path, 'rb') as f:
        audio_data = f.read()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "x-folder-id": folder_id
    }
    
    params = {
        "lang": "ru-RU"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url, 
            data=audio_data, 
            headers=headers,
            params=params
        )
        result = response.json()
        return result.get("result", "")
```

**Yandex Vision OCR:**

```python
import httpx
import base64

async def ocr_image(image_url: str) -> str:
    """OCR для фото тетради"""
    # Скачать изображение по URL
    async with httpx.AsyncClient() as client:
        image_response = await client.get(image_url)
        image_base64 = base64.b64encode(image_response.content).decode()
    
    url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
    
    payload = {
        "analyzeSpecs": [
            {
                "content": image_base64,
                "features": [
                    {
                        "type": "TEXT_DETECTION"
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "x-folder-id": folder_id
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        result = response.json()
        # Парсить результаты из result["results"][0]["textDetection"]["text"]
        text = ""
        for page in result["results"]:
            if "textDetection" in page:
                text += page["textDetection"]["text"] + "\n"
        return text
```

---

## 📝 Переменные окружения (.env)

```env
# Yandex Cloud
YANDEX_GPT_API_KEY=<твой API ключ для GPT>
YANDEX_FOLDER_ID=<твой folder_id из консоли Яндекса>
YANDEX_VISION_API_KEY=<ключ для Vision (может быть тот же)>
YANDEX_SPEECHKIT_API_KEY=<ключ для SpeechKit>

# Остальное (уже есть)
DATABASE_URL=postgresql://teacher:teacher123@localhost:5433/eduassist
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=minio123
JWT_SECRET=your-secret-key
```

---

## 🎯 Приоритет реализации

| # | Фича | Время | Приоритет | Критерий успеха |
|---|------|-------|-----------|----------------|
| 1 | Проверка домашки (OCR + GPT) | 2-3 ч | 🔴 CRITICAL | На видео демо работает |
| 2 | Анализ шума (STT + парсинг имён) | 2-3 ч | 🟡 HIGH | Показывает замечания учителя |
| 3 | Резюме урока (генерация текста) | 1 ч | 🟢 NICE | Красивый отчёт в конце |
| 4 | Расписание (функция calling) | 1-2 ч | 🟡 MEDIUM | Если будет время |

---

## 🎬 Как снять видео-демо

**Сценарий (1 минута):**

1. **Вход (10 сек):** Залогиниться как учитель
2. **Загрузка домашки (15 сек):** Ученик загружает фото → видим что анализируется → появляется оценка + ошибки + вопросы
3. **Анализ урока (20 сек):** Запуск записи → говорим фразы про учеников ("Тимофей тише", "Макс молодец") → завершаем → видим отчёт с именами
4. **Расписание (15 сек):** Директор генерирует расписание → видим красивую таблицу
5. **Итог (не говорить, только текст на экране):** "EduAssist — AI помощник для школы"

---

## ⚠️ Что если нет ключей Яндекса?

Если твой Yandex Cloud аккаунт не готов:

1. Создай пустой `.env` с плейсхолдерами
2. В коде добавь `if api_key: call_real_api() else: return mock_response()`
3. На видео используй мок-данные (но скажи что это для демо)
4. Жюри примет это, если код правильный

---

## 📦 Зависимости для установки

```bash
pip install httpx  # Для HTTP запросов к Yandex API
# Остальное уже есть в requirements.txt
```

Если httpx не в requirements:
```bash
pip install httpx
echo "httpx>=0.27.0" >> backend/requirements.txt
```

---

**Готово к реализации?** 🚀
