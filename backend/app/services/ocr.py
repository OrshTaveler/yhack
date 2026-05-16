"""Yandex Vision OCR — распознавание текста с фото (в т.ч. рукописного)."""

from __future__ import annotations

import base64
import json
import logging
import urllib.error
import urllib.request

from app.config import get_settings

logger = logging.getLogger(__name__)

OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"

# Заглушка на случай отсутствия ключа / падения API — демо не упадёт
_FALLBACK_TEXT = (
    "Фотосинтез — это процесс, при котором растения создают питательные "
    "вещества из углекислого газа и воды с помощью солнечного света."
)


def recognize(image_bytes: bytes, mime: str = "JPEG") -> str:
    """Фото → распознанный текст. При ошибке возвращает заглушку."""
    settings = get_settings()
    if not settings.yandex_api_key or not settings.yandex_folder_id:
        logger.warning("OCR: нет ключей Yandex — использую заглушку")
        return _FALLBACK_TEXT

    payload = {
        "mimeType": mime,
        "languageCodes": ["ru", "en"],
        "model": "handwritten",  # модель для рукописного текста
        "content": base64.b64encode(image_bytes).decode("utf-8"),
    }
    req = urllib.request.Request(
        OCR_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {settings.yandex_api_key}",
            "x-folder-id": settings.yandex_folder_id,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = (
            data.get("result", {})
            .get("textAnnotation", {})
            .get("fullText", "")
        )
        return text.strip() or _FALLBACK_TEXT
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        logger.warning("OCR упал (%s) — использую заглушку", e)
        return _FALLBACK_TEXT
