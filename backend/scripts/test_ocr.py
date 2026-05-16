"""
Этап 1: Проверка Yandex Vision OCR (отдельно от приложения).

Запуск:
    python scripts/test_ocr.py путь/к/фото.jpg

Перед запуском задай переменные окружения (или впиши ниже):
    YANDEX_API_KEY   — API-ключ из AI Studio
    YANDEX_FOLDER_ID — ID папки (b1g...)

Windows PowerShell:
    $env:YANDEX_API_KEY="твой_ключ"
    $env:YANDEX_FOLDER_ID="b1g..."
    python scripts/test_ocr.py photo.jpg
"""

import base64
import json
import os
import sys
import urllib.request
import urllib.error

# Принудительно UTF-8 для вывода (Windows-консоль по умолчанию cp1251)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── Настройки ───────────────────────────────────────────────
API_KEY = os.getenv("YANDEX_API_KEY", "")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")

OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"


def detect_mime(path: str) -> str:
    """Определяет mimeType по расширению файла."""
    lower = path.lower()
    if lower.endswith(".png"):
        return "PNG"
    if lower.endswith(".pdf"):
        return "PDF"
    return "JPEG"


def recognize(image_path: str) -> None:
    if not API_KEY or not FOLDER_ID:
        print("ОШИБКА: задай YANDEX_API_KEY и YANDEX_FOLDER_ID в переменных окружения.")
        sys.exit(1)

    if not os.path.exists(image_path):
        print(f"ОШИБКА: файл не найден: {image_path}")
        sys.exit(1)

    with open(image_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    # model: "handwritten" — для рукописного текста, "page" — для печатного
    model = os.getenv("OCR_MODEL", "handwritten")
    payload = {
        "mimeType": detect_mime(image_path),
        "languageCodes": ["ru", "en"],
        "model": model,
        "content": content_b64,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}",
        "x-folder-id": FOLDER_ID,
        "x-data-logging-enabled": "true",
    }

    req = urllib.request.Request(
        OCR_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    print(f"→ Отправляю {image_path} в Vision OCR...")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}: {e.reason}")
        print(e.read().decode("utf-8", errors="replace"))
        sys.exit(1)
    except Exception as e:
        print(f"✗ Ошибка сети: {e}")
        sys.exit(1)

    data = json.loads(raw)
    text = (
        data.get("result", {})
        .get("textAnnotation", {})
        .get("fullText", "")
    )

    print("\n" + "=" * 50)
    print("РАСПОЗНАННЫЙ ТЕКСТ:")
    print("=" * 50)
    print(text if text else "(пусто — проверь фото)")
    print("=" * 50)
    print(f"\n✓ OCR работает. Символов распознано: {len(text)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python scripts/test_ocr.py путь/к/фото.jpg")
        sys.exit(1)
    recognize(sys.argv[1])
