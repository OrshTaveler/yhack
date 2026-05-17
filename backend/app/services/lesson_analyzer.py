"""Анализ урока через YandexGPT.

Вход — расшифровка речи учителя (STT). Модель:
  • находит упоминания учеников по именам/фамилиям + контекст (похвала/замечание);
  • выделяет тезисы урока;
  • вытаскивает домашнее задание по ключевым словам.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

SYSTEM_PROMPT = (
    "Ты ассистент учителя. На вход — расшифровка речи учителя на уроке (STT, "
    "возможны искажения распознавания). Проанализируй её и верни СТРОГО JSON "
    "без markdown и пояснений снаружи:\n"
    '{"students": [{"name": "<имя/фамилия ученика>", '
    '"type": "praise|remark", "quote": "<фраза учителя>"}], '
    '"summary": ["<тезис урока>", ...], '
    '"homework": "<что задано на дом, или пустая строка>"}\n'
    "Правила:\n"
    "- В students попадают ТОЛЬКО ученики, к которым учитель обратился по имени "
    "или фамилии. type=praise — похвала («молодец», «отлично»), "
    "type=remark — замечание («тише», «не отвлекайся»).\n"
    "- summary — 3-6 кратких тезисов: тема урока, что разобрали.\n"
    "- homework — задание на дом, если учитель его называл; иначе пустая строка.\n"
    "- Если учеников по именам не упоминали — students пустой массив."
)


@dataclass
class StudentMention:
    name: str
    type: str  # praise | remark
    quote: str


@dataclass
class LessonReport:
    students: list[StudentMention] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
    homework: str = ""
    ok: bool = False
    note: str = ""


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```")
    text = text.removesuffix("```")
    return text.strip()


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = _strip_code_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        return json.loads(match.group(0))
    raise json.JSONDecodeError("Нет JSON в ответе модели", text, 0)


def analyze_lesson(transcript: str) -> LessonReport:
    """Расшифровка урока → структурированный отчёт через YandexGPT."""
    transcript = (transcript or "").strip()
    if not transcript:
        return LessonReport(ok=False, note="Речь учителя не распознана.")

    settings = get_settings()
    if not settings.yandex_api_key or not settings.yandex_folder_id:
        return LessonReport(ok=False, note="Нет ключей Yandex — анализ не выполнен.")

    payload = {
        "modelUri": f"gpt://{settings.yandex_folder_id}/yandexgpt-lite/latest",
        "completionOptions": {"stream": False, "temperature": 0.2, "maxTokens": 1500},
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": f"Расшифровка урока:\n\n{transcript}"},
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        answer = data["result"]["alternatives"][0]["message"]["text"]
        parsed = _parse_json(answer)

        students = [
            StudentMention(
                name=str(s.get("name", "")).strip(),
                type=str(s.get("type", "remark")).strip(),
                quote=str(s.get("quote", "")).strip(),
            )
            for s in (parsed.get("students") or [])
            if isinstance(s, dict) and str(s.get("name", "")).strip()
        ]
        summary = [str(x).strip() for x in (parsed.get("summary") or []) if str(x).strip()]
        homework = str(parsed.get("homework") or "").strip()

        return LessonReport(
            students=students,
            summary=summary,
            homework=homework,
            ok=True,
        )
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
        logger.warning("Анализ урока упал (%s)", exc)
        return LessonReport(ok=False, note="Ошибка YandexGPT при анализе урока.")
