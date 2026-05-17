"""Yandex AI Search (vector store): семантический поиск по индексу из консоли."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

from app.config import Settings, get_settings
from app.services.knowledge import format_chunks_context

logger = logging.getLogger(__name__)

LLM_API_BASE = "https://llm.api.cloud.yandex.net/v1"
SEARCH_RESPONSES_URL = f"{LLM_API_BASE}/responses"

SEARCH_RETRY_ATTEMPTS = 3
SEARCH_RETRY_BASE_DELAY_SEC = 1.0


@dataclass
class RetrievalResult:
    context: str
    source: str  # ai_search | unavailable
    chunks: list[str]


def _ai_search_configured() -> bool:
    settings = get_settings()
    return bool(settings.yandex_api_key and settings.yandex_folder_id and settings.yandex_knowledge_index_id)


def _headers(settings: Settings, content_type: str = "application/json") -> dict[str, str]:
    return {
        "Authorization": f"Api-Key {settings.yandex_api_key}",
        "x-folder-id": settings.yandex_folder_id,
        "Content-Type": content_type,
    }


def _http_error_detail(exc: BaseException, url: str) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            body = ""
        req_url = getattr(exc, "url", None) or url
        return f"POST {req_url} → HTTP {exc.code}: {body[:500] or exc.reason}"
    if isinstance(exc, urllib.error.URLError):
        return f"POST {url} → {exc.reason}"
    return f"POST {url} → {exc}"


def _request_json(
    url: str,
    payload: dict[str, Any],
    settings: Settings,
    *,
    timeout: int = 90,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers=_headers(settings),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_search_chunks(response: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for item in response.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "file_search_call":
            continue
        for result in item.get("results") or []:
            if not isinstance(result, dict):
                continue
            text = result.get("text")
            if text:
                texts.append(str(text).strip())
    return texts


def _file_search_request(
    settings: Settings,
    instructions: str,
    user_input: str,
) -> dict[str, Any]:
    payload = {
        "model": f"gpt://{settings.yandex_folder_id}/yandexgpt-lite/latest",
        "instructions": instructions,
        "tools": [
            {
                "type": "file_search",
                "vector_store_ids": [settings.yandex_knowledge_index_id],
            }
        ],
        "input": user_input,
    }
    return _request_json(SEARCH_RESPONSES_URL, payload, settings, timeout=120)


def _unavailable_result(subject_name: str, grade: Optional[int], reason: str) -> RetrievalResult:
    grade_label = f" ({grade} класс)" if grade is not None else ""
    context = (
        f"Справочные факты по предмету «{subject_name}»{grade_label} временно недоступны "
        f"(Yandex AI Search: {reason})."
    )
    return RetrievalResult(context=context, source="unavailable", chunks=[])


def retrieve_context(
    query: str,
    subject_name: str,
    grade: Optional[int] = None,
    limit: int = 8,
) -> RetrievalResult:
    """Ищет релевантные факты только в Yandex AI Search (с ретраями)."""
    if not _ai_search_configured():
        logger.warning("AI Search: не заданы YANDEX_API_KEY, FOLDER_ID или KNOWLEDGE_INDEX_ID")
        return _unavailable_result(subject_name, grade, "не настроен индекс")

    settings = get_settings()
    search_query = (query or "").strip()
    if not search_query:
        search_query = f"проверка домашнего задания по предмету {subject_name}"

    grade_hint = f", класс {grade}" if grade is not None else ""
    instructions = (
        f"Найди в индексе справочные факты только по предмету «{subject_name}»{grade_hint}. "
        "Игнорируй факты по другим предметам."
    )
    user_input = (
        f"Предмет: {subject_name}{grade_hint}\n"
        f"Текст работы ученика:\n{search_query}\n\n"
        "Верни наиболее релевантные учебные факты для проверки этой работы."
    )

    index_id = settings.yandex_knowledge_index_id
    last_error = "неизвестная ошибка"
    for attempt in range(1, SEARCH_RETRY_ATTEMPTS + 1):
        logger.info(
            "AI Search: попытка %s/%s POST %s (index=%s, subject=%s)",
            attempt,
            SEARCH_RETRY_ATTEMPTS,
            SEARCH_RESPONSES_URL,
            index_id,
            subject_name,
        )
        try:
            response = _file_search_request(settings, instructions, user_input)
            chunks = _extract_search_chunks(response)[:limit]
            if chunks:
                context = format_chunks_context(subject_name, chunks, grade)
                if attempt > 1:
                    logger.info(
                        "AI Search: успех с попытки %s/%s POST %s",
                        attempt,
                        SEARCH_RETRY_ATTEMPTS,
                        SEARCH_RESPONSES_URL,
                    )
                return RetrievalResult(context=context, source="ai_search", chunks=chunks)
            last_error = f"POST {SEARCH_RESPONSES_URL} → пустой ответ (нет чанков)"
            logger.warning(
                "AI Search: попытка %s/%s — %s",
                attempt,
                SEARCH_RETRY_ATTEMPTS,
                last_error,
            )
        except (urllib.error.URLError, json.JSONDecodeError, KeyError, ValueError) as exc:
            last_error = _http_error_detail(exc, SEARCH_RESPONSES_URL)
            logger.warning(
                "AI Search: попытка %s/%s — %s",
                attempt,
                SEARCH_RETRY_ATTEMPTS,
                last_error,
            )

        if attempt < SEARCH_RETRY_ATTEMPTS:
            delay = SEARCH_RETRY_BASE_DELAY_SEC * (2 ** (attempt - 1))
            logger.info(
                "AI Search: повтор через %.1f с → POST %s",
                delay,
                SEARCH_RESPONSES_URL,
            )
            time.sleep(delay)

    logger.error(
        "AI Search: все %s попыток к %s неудачны (%s)",
        SEARCH_RETRY_ATTEMPTS,
        SEARCH_RESPONSES_URL,
        last_error,
    )
    return _unavailable_result(subject_name, grade, last_error)
