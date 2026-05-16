"""text.ru — проверка текста на списывание (антиплагиат)."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from app.config import get_settings

logger = logging.getLogger(__name__)

TEXTRU_URL = "https://api.text.ru/post"


@dataclass
class PlagiarismResult:
    """Результат проверки антиплагиата."""

    unique: float  # % уникальности (0..100)
    sources: list[dict] = field(default_factory=list)  # [{url, plagiat}]
    ok: bool = True  # False → проверка не удалась, данные приблизительные


def _post(params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        TEXTRU_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check(text: str, max_attempts: int = 15, delay: int = 6) -> PlagiarismResult:
    """Проверяет текст на уникальность через text.ru.

    text.ru работает в два шага: отправка текста → опрос результата.
    При ошибке возвращает ok=False с нейтральным значением.
    """
    settings = get_settings()
    if not settings.textru_userkey:
        logger.warning("Антиплагиат: нет textru_userkey — пропускаю")
        return PlagiarismResult(unique=100.0, ok=False)

    try:
        # Шаг 1 — отправка
        submit = _post({"userkey": settings.textru_userkey, "text": text})
        uid = submit.get("text_uid")
        if not uid:
            logger.warning("Антиплагиат: text.ru не принял текст: %s", submit)
            return PlagiarismResult(unique=100.0, ok=False)

        # Шаг 2 — опрос результата
        for _ in range(max_attempts):
            result = _post(
                {
                    "userkey": settings.textru_userkey,
                    "uid": uid,
                    "jsonvisible": "detail",
                }
            )
            if result.get("error_code") == 181:  # ещё в очереди
                time.sleep(delay)
                continue

            unique = float(result.get("text_unique", 100.0))
            detail = json.loads(result.get("result_json", "{}"))
            sources = [
                {"url": u.get("url"), "plagiat": u.get("plagiat")}
                for u in detail.get("urls", [])[:10]
            ]
            return PlagiarismResult(unique=unique, sources=sources, ok=True)

        logger.warning("Антиплагиат: text.ru не успел проверить")
        return PlagiarismResult(unique=100.0, ok=False)

    except (urllib.error.URLError, json.JSONDecodeError, ValueError) as e:
        logger.warning("Антиплагиат упал (%s)", e)
        return PlagiarismResult(unique=100.0, ok=False)


def verdict(unique: float) -> str:
    """Текстовый вердикт по проценту уникальности."""
    if unique > 70:
        return "Написано самостоятельно"
    if unique >= 40:
        return "Частично заимствовано"
    return "Списано из интернета"
