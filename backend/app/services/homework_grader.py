"""Подсветка проблемных мест в домашней работе через YandexGPT (без выставления оценки)."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional

from app.config import get_settings
from app.models.homework import HomeworkSubmission
from app.services.knowledge import build_homework_review_prompt

logger = logging.getLogger(__name__)

GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

SYSTEM_PROMPT = (
    "Ты помощник учителя. НЕ ставь оценку и НЕ пиши итоговый балл. "
    "Твоя задача — указать учителю проблемные места в решении ученика: "
    "ошибки, пробелы, неточности, сомнительные шаги. "
    "Сверяйся со справочными фактами из запроса. "
    "Если серьёзных замечаний нет — так и напиши в summary, highlights может быть пустым. "
    "Ответь СТРОГО JSON без markdown и пояснений снаружи: "
    '{"summary": "<1-2 предложения для учителя>", '
    '"highlights": [{"fragment": "<цитата или место в решении>", '
    '"problem": "<в чём проблема>", "note": "<на что обратить внимание>"}], '
    '"positives": ["<что сделано верно>", ...]}'
)


@dataclass
class HomeworkReviewResult:
    comment: str = ""
    highlights: list[str] = field(default_factory=list)
    prompt: str = ""
    ok: bool = False


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    text = text.removeprefix("```json").removeprefix("```")
    text = text.removesuffix("```")
    return text.strip()


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = _strip_code_fence(text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        parsed = json.loads(match.group(0))
        if isinstance(parsed, dict):
            return parsed
    raise json.JSONDecodeError("Нет JSON-объекта в ответе модели", text, 0)


def _format_teacher_comment(parsed: dict[str, Any]) -> tuple[str, list[str]]:
    summary = str(parsed.get("summary") or "").strip()
    lines: list[str] = []
    highlight_lines: list[str] = []

    raw_highlights = parsed.get("highlights") or []
    if isinstance(raw_highlights, list):
        for i, item in enumerate(raw_highlights, 1):
            if isinstance(item, str) and item.strip():
                highlight_lines.append(item.strip())
                lines.append(f"{i}. {item.strip()}")
                continue
            if not isinstance(item, dict):
                continue
            fragment = str(item.get("fragment") or item.get("place") or "").strip()
            problem = str(item.get("problem") or item.get("issue") or "").strip()
            note = str(item.get("note") or item.get("hint_for_teacher") or "").strip()
            parts = [p for p in (fragment, problem) if p]
            line = f"{i}. " + " — ".join(parts) if parts else f"{i}."
            if note:
                line += f" Обратите внимание: {note}"
            if line.strip() != f"{i}.":
                highlight_lines.append(line)
                lines.append(line)

    positives = parsed.get("positives") or []
    positive_lines: list[str] = []
    if isinstance(positives, list):
        positive_lines = [str(p).strip() for p in positives if str(p).strip()]

    blocks: list[str] = []
    if summary:
        blocks.append(summary)
    if lines:
        blocks.append("Проблемные места:\n" + "\n".join(lines))
    elif summary and not lines:
        pass
    elif not summary:
        blocks.append("Существенных замечаний не найдено.")
    if positive_lines:
        blocks.append("Сильные стороны: " + "; ".join(positive_lines))

    return "\n\n".join(blocks), highlight_lines


def review_homework(
    submission: HomeworkSubmission,
    subject_name: str,
    class_grade: Optional[int],
    knowledge_context: str,
    ocr_text: Optional[str] = None,
    text_unique: Optional[float] = None,
    ai_probability: Optional[float] = None,
    image_url: Optional[str] = None,
) -> HomeworkReviewResult:
    prompt = build_homework_review_prompt(
        submission,
        subject_name,
        class_grade,
        knowledge_context,
        ocr_text=ocr_text,
        text_unique=text_unique,
        ai_probability=ai_probability,
        image_url=image_url,
    )
    settings = get_settings()
    if not settings.yandex_api_key or not settings.yandex_folder_id:
        logger.warning("Review: нет ключей Yandex — замечания не сформированы")
        return HomeworkReviewResult(
            comment="Замечания ИИ не сформированы (нет ключей Yandex).",
            prompt=prompt,
            ok=False,
        )

    payload = {
        "modelUri": f"gpt://{settings.yandex_folder_id}/yandexgpt-lite/latest",
        "completionOptions": {"stream": False, "temperature": 0.2, "maxTokens": 800},
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": prompt},
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
        parsed = _parse_json_object(answer)
        comment, highlights = _format_teacher_comment(parsed)
        return HomeworkReviewResult(
            comment=comment,
            highlights=highlights,
            prompt=prompt,
            ok=True,
        )
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
        logger.warning("Review упал (%s)", exc)
        return HomeworkReviewResult(
            comment="Замечания ИИ не сформированы (ошибка YandexGPT).",
            prompt=prompt,
            ok=False,
        )


# Обратная совместимость для старых импортов
GradingResult = HomeworkReviewResult


def grade_homework(*args: Any, **kwargs: Any) -> HomeworkReviewResult:
    return review_homework(*args, **kwargs)
