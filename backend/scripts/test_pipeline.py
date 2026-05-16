"""
Этап 3: Полный пайплайн — фото → OCR → text.ru → вердикт.

Репетиция перед интеграцией в приложение.

Запуск:
    python scripts/test_pipeline.py путь/к/фото.jpg

Переменные окружения:
    YANDEX_API_KEY, YANDEX_FOLDER_ID  — для Vision OCR
    TEXTRU_USERKEY                     — для антиплагиата text.ru
"""

import base64
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

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")
TEXTRU_USERKEY = os.getenv("TEXTRU_USERKEY", "")

OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"
TEXTRU_URL = "https://api.text.ru/post"


# ─────────────────────────────────────────────────────────────
# Шаг 1: OCR — фото → текст
# ─────────────────────────────────────────────────────────────
def ocr_recognize(image_path: str) -> str:
    with open(image_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    mime = "PNG" if image_path.lower().endswith(".png") else "JPEG"
    payload = {
        "mimeType": mime,
        "languageCodes": ["ru", "en"],
        "model": "handwritten",  # модель для рукописи
        "content": content_b64,
    }
    req = urllib.request.Request(
        OCR_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "x-folder-id": YANDEX_FOLDER_ID,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("result", {}).get("textAnnotation", {}).get("fullText", "")


# ─────────────────────────────────────────────────────────────
# Шаг 2: text.ru — текст → антиплагиат
# ─────────────────────────────────────────────────────────────
def _textru_post(params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        TEXTRU_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def textru_check(text: str) -> dict:
    submit = _textru_post({"userkey": TEXTRU_USERKEY, "text": text})
    uid = submit.get("text_uid")
    if not uid:
        return {"error": json.dumps(submit, ensure_ascii=False)}

    for i in range(1, 16):
        result = _textru_post(
            {"userkey": TEXTRU_USERKEY, "uid": uid, "jsonvisible": "detail"}
        )
        if result.get("error_code") == 181:
            print(f"  ...text.ru проверяет, попытка {i}/15")
            time.sleep(6)
            continue
        return result
    return {"error": "timeout"}


# ─────────────────────────────────────────────────────────────
# Вердикт
# ─────────────────────────────────────────────────────────────
def verdict(unique: float) -> str:
    if unique > 70:
        return "✅ Написано самостоятельно"
    if unique >= 40:
        return "🟡 Частично заимствовано"
    return "🔴 Списано из интернета"


def main(image_path: str) -> None:
    if not (YANDEX_API_KEY and YANDEX_FOLDER_ID and TEXTRU_USERKEY):
        print("ОШИБКА: задай YANDEX_API_KEY, YANDEX_FOLDER_ID, TEXTRU_USERKEY")
        sys.exit(1)
    if not os.path.exists(image_path):
        print(f"ОШИБКА: файл не найден: {image_path}")
        sys.exit(1)

    print("=" * 55)
    print("ПАЙПЛАЙН: фото → OCR → антиплагиат")
    print("=" * 55)

    # ── Шаг 1 ──
    print("\n[1/2] Vision OCR: распознаю текст с фото...")
    text = ocr_recognize(image_path)
    if not text.strip():
        print("✗ OCR не распознал текст")
        sys.exit(1)
    print(f"  Распознано символов: {len(text)}")
    print(f"  Текст:\n  «{text.strip()}»")

    # ── Шаг 2 ──
    print("\n[2/2] text.ru: проверяю на списывание...")
    result = textru_check(text)
    if "error" in result:
        print(f"✗ Ошибка text.ru: {result['error']}")
        sys.exit(1)

    unique = float(result.get("text_unique", 0))
    detail = json.loads(result.get("result_json", "{}"))
    urls = detail.get("urls", [])

    print("\n" + "=" * 55)
    print("РЕЗУЛЬТАТ ПРОВЕРКИ")
    print("=" * 55)
    print(f"Уникальность:  {unique}%")
    print(f"Вердикт:       {verdict(unique)}")
    if urls:
        print(f"\nНайдено совпадений с источниками: {len(urls)}")
        for u in urls[:5]:
            print(f"  • {u['plagiat']}%  {u['url']}")
    print("=" * 55)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scripts/test_pipeline.py путь/к/фото.jpg")
        sys.exit(1)
    main(sys.argv[1])
