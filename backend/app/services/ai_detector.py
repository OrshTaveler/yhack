"""AI-детектор на базе YandexGPT — оценка, написан ли текст нейросетью."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass

from app.config import get_settings

logger = logging.getLogger(__name__)

GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

SYSTEM_PROMPT = (
    "Ты эксперт по определению AI-сгенерированного текста. "
    "Оцени, насколько вероятно, что текст написан нейросетью (ChatGPT, "
    "YandexGPT), а не школьником вручную. Признаки AI: гладкие обтекаемые "
    "формулировки, отсутствие живых ошибок, шаблонные вводные обороты, "
    "идеальная структура. Признаки человека: разговорные слова, неровный "
    "стиль, мелкие ошибки. Ответь СТРОГО в формате JSON без пояснений: "
    '{"ai_probability": <число 0-100>, "reason": "<краткая причина>"}'
)


@dataclass
class AiDetectionResult:
    """Результат AI-детекции."""

    probability: float  # % вероятности AI (0..100)
    reason: str
    ok: bool = True


def _strip_code_fence(text: str) -> str:
    """Убирает обёртку ```json ... ``` из ответа модели."""
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```")
    text = text.removesuffix("```")
    return text.strip()


def detect(text: str) -> AiDetectionResult:
    """Оценивает вероятность AI-генерации текста через YandexGPT."""
    settings = get_settings()
    if not settings.yandex_api_key or not settings.yandex_folder_id:
        logger.warning("AI-детектор: нет ключей Yandex — пропускаю")
        return AiDetectionResult(probability=0.0, reason="проверка не выполнена", ok=False)

    payload = {
        "modelUri": f"gpt://{settings.yandex_folder_id}/yandexgpt-lite/latest",
        "completionOptions": {"stream": False, "temperature": 0.1, "maxTokens": 200},
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
            "Authorization": f"Api-Key {settings.yandex_api_key}",
            "x-folder-id": settings.yandex_folder_id,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        answer = data["result"]["alternatives"][0]["message"]["text"]
        parsed = json.loads(_strip_code_fence(answer))
        return AiDetectionResult(
            probability=float(parsed.get("ai_probability", 0)),
            reason=str(parsed.get("reason", "")),
            ok=True,
        )
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning("AI-детектор упал (%s)", e)
        return AiDetectionResult(probability=0.0, reason="проверка не выполнена", ok=False)
