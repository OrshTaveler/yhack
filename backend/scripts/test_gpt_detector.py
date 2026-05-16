"""
Этап 3.5: AI-детектор через YandexGPT.

Просим YandexGPT оценить, насколько вероятно, что текст написан
нейросетью, а не школьником. Работает с русским языком нативно.

Запуск:
    python scripts/test_gpt_detector.py

Прогоняет два текста:
  1. «Живой» ученический — ждём низкий %
  2. Гладкий AI-текст     — ждём высокий %

Переменные окружения:
    YANDEX_API_KEY, YANDEX_FOLDER_ID
"""

import json
import os
import sys
import urllib.request
import urllib.error

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

API_KEY = os.getenv("YANDEX_API_KEY", "")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")
GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Промпт-инструкция для модели
SYSTEM_PROMPT = (
    "Ты эксперт по определению AI-сгенерированного текста. "
    "Оцени, насколько вероятно, что текст написан нейросетью (ChatGPT, "
    "YandexGPT), а не школьником вручную. Признаки AI: гладкие "
    "обтекаемые формулировки, отсутствие живых ошибок, шаблонные "
    "вводные обороты, идеальная структура. Признаки человека: "
    "разговорные слова, неровный стиль, мелкие ошибки. "
    "Ответь СТРОГО в формате JSON без пояснений: "
    '{"ai_probability": <число 0-100>, "reason": "<краткая причина>"}'
)

HUMAN_TEXT = (
    "Вчера делал домашку по физике, чет вообще не врубился в задачу "
    "про трение. Спросил у бати — он тоже не помнит. В итоге кое-как "
    "решил, вроде правильно получилось."
)

AI_TEXT = (
    "Фотосинтез представляет собой сложный биологический процесс, "
    "играющий ключевую роль в жизнедеятельности растений. Данный "
    "процесс обеспечивает преобразование солнечной энергии и имеет "
    "важное значение для поддержания экологического баланса планеты."
)


def call_gpt(text: str) -> dict:
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.1,
            "maxTokens": 200,
        },
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": f"Проверь текст:\n\n{text}"},
        ],
    }
    req = urllib.request.Request(
        GPT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {API_KEY}",
            "x-folder-id": FOLDER_ID,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    answer = data["result"]["alternatives"][0]["message"]["text"]
    # Модель может обернуть JSON в ```json ... ``` — вычищаем
    answer = answer.strip().removeprefix("```json").removeprefix("```")
    answer = answer.removesuffix("```").strip()
    return json.loads(answer)


def run_one(label: str, text: str) -> None:
    print(f"\n— {label} —")
    print(f"  Текст: {text[:65]}...")
    try:
        result = call_gpt(text)
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}")
        return
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  ✗ Не разобрал ответ модели: {e}")
        return
    print(f"  → Вероятность AI: {result.get('ai_probability')}%")
    print(f"  → Причина: {result.get('reason')}")


if __name__ == "__main__":
    if not (API_KEY and FOLDER_ID):
        print("ОШИБКА: задай YANDEX_API_KEY и YANDEX_FOLDER_ID")
        sys.exit(1)

    print("=" * 55)
    print("ТЕСТ AI-детектора (YandexGPT)")
    print("=" * 55)
    run_one("Живой ученический текст (ждём низкий %)", HUMAN_TEXT)
    run_one("Гладкий AI-текст (ждём высокий %)", AI_TEXT)
    print("\n" + "=" * 55)
