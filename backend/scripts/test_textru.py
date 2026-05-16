"""
Этап 2: Проверка text.ru — российский сервис антиплагиата / детекции нейросетей.

Запуск:
    python scripts/test_textru.py

Перед запуском получи userkey:
    1. Зарегистрируйся на https://text.ru
    2. Личный кабинет → раздел «API» → скопируй userkey
    3. Задай переменную:
       PowerShell:  $env:TEXTRU_USERKEY="твой_ключ"

API text.ru двухшаговый:
    1) POST api.text.ru/post  с text+userkey  → возвращает text_uid
    2) POST api.text.ru/post  с uid+userkey   → возвращает результат
       (пока текст в очереди — отдаёт error_code 181, нужно опрашивать)
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

USERKEY = os.getenv("TEXTRU_USERKEY", "")
API_URL = "https://api.text.ru/post"

# Тестовый текст — кусок «домашней работы»
SAMPLE_TEXT = (
    "Сила трения — это сила, которая возникает при движении одного тела "
    "по поверхности другого и направлена против движения. Она зависит от "
    "того, насколько шероховатые поверхности и с какой силой они прижаты "
    "друг к другу. Трение бывает полезным и вредным. Например, без трения "
    "мы не смогли бы ходить, потому что ноги скользили бы по земле."
)


def _post(params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def submit_text(text: str) -> str:
    """Шаг 1 — отправляем текст, получаем uid."""
    result = _post({"userkey": USERKEY, "text": text})
    if "text_uid" not in result:
        print(f"✗ Ошибка отправки: {json.dumps(result, ensure_ascii=False)}")
        sys.exit(1)
    return result["text_uid"]


def fetch_result(uid: str, attempts: int = 15, delay: int = 6) -> dict:
    """Шаг 2 — опрашиваем результат, пока текст в очереди."""
    for i in range(1, attempts + 1):
        result = _post({"userkey": USERKEY, "uid": uid, "jsonvisible": "detail"})
        if result.get("error_code") == 181:
            print(f"  ...текст в очереди, попытка {i}/{attempts}")
            time.sleep(delay)
            continue
        return result
    print("✗ Результат не готов за отведённое время")
    sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("ТЕСТ text.ru")
    print("=" * 50)

    if not USERKEY:
        print("ОШИБКА: задай TEXTRU_USERKEY (получи на text.ru → API)")
        sys.exit(1)

    print("→ Шаг 1: отправляю текст на проверку...")
    uid = submit_text(SAMPLE_TEXT)
    print(f"  text_uid = {uid}")

    print("→ Шаг 2: жду результат проверки...")
    result = fetch_result(uid)

    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТ:")
    print("=" * 50)
    unique = result.get("text_unique", "—")
    print(f"Уникальность: {unique}%")
    # Полный ответ — чтобы увидеть, есть ли поле детекции нейросетей
    print(f"\nПолный ответ:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
    print("=" * 50)
