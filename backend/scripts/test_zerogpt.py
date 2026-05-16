"""
Этап 2: Проверка ZeroGPT — детектор AI-сгенерированного текста.

Запуск:
    python scripts/test_zerogpt.py

Скрипт прогоняет два текста:
  1. Явно «человеческий» — должен дать низкий % AI
  2. Явно «AI-шный» — должен дать высокий % AI

ZeroGPT API:
  Эндпоинт: https://api.zerogpt.com/api/detect/detectText
  Официальный API требует ключ (заголовок ApiKey).
  Ключ берётся на https://zerogpt.com → раздел API.

  Если ключа нет — задай ZEROGPT_API_KEY пустым, скрипт попробует
  публичный вызов (может не сработать из-за лимитов).
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

ZEROGPT_API_KEY = os.getenv("ZEROGPT_API_KEY", "")
ZEROGPT_URL = "https://api.zerogpt.com/api/detect/detectText"

# Тест 1 — текст, написанный человеком (с ошибками, живой)
HUMAN_TEXT = (
    "Вчера я делал домашку по физике и чет вообще не понял задачу про "
    "силу трения. Спросил у бати, он тоже не помнит формулы. В итоге "
    "списал кусок у Сашки, но половину переписал по-своему."
)

# Тест 2 — текст, типичный для нейросети (гладкий, структурный)
AI_TEXT = (
    "Сила трения представляет собой фундаментальное физическое явление, "
    "возникающее при взаимодействии двух поверхностей. Данный процесс "
    "играет ключевую роль в механике и имеет важное практическое значение. "
    "Рассмотрим основные аспекты данного явления более подробно."
)


def detect(text: str) -> dict:
    payload = json.dumps({"input_text": text}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if ZEROGPT_API_KEY:
        headers["ApiKey"] = ZEROGPT_API_KEY

    req = urllib.request.Request(
        ZEROGPT_URL, data=payload, headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_one(label: str, text: str) -> None:
    print(f"\n— {label} —")
    print(f"  Текст: {text[:70]}...")
    try:
        data = detect(text)
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP {e.code}: {e.reason}")
        print("  " + e.read().decode("utf-8", errors="replace")[:300])
        return
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return

    # Печатаем сырой ответ целиком — чтобы понять структуру
    print(f"  Сырой ответ: {json.dumps(data, ensure_ascii=False)[:500]}")
    body = data.get("data") or data
    if isinstance(body, dict):
        fake = body.get("fakePercentage", body.get("isGPTGenerated"))
        print(f"  → Вероятность AI: {fake}%")


if __name__ == "__main__":
    print("=" * 50)
    print("ТЕСТ ZeroGPT")
    print("=" * 50)
    if not ZEROGPT_API_KEY:
        print("⚠ ZEROGPT_API_KEY не задан — пробуем публичный вызов")
    run_one("Человеческий текст (ждём низкий %)", HUMAN_TEXT)
    run_one("AI-текст (ждём высокий %)", AI_TEXT)
    print("\n" + "=" * 50)
