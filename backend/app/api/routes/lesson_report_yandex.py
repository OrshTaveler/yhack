from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

YANDEX_COMPLETION_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

LESSON_REPORT_RETRY_ATTEMPTS = 3
LESSON_REPORT_RETRY_BASE_DELAY_SEC = 1.0

YANDEX_LESSON_REPORT_PROMPT = """
Ты помощник учителя. Проанализируй JSON-таймлайн урока.

В JSON есть окна по минутам:
- average_loudness_dbfs — средний уровень шума за минуту;
- teacher_speaking_percent — процент времени, когда говорил учитель;
- teacher_transcript — расшифровка речи учителя за минуту;
- samples_count — количество аудио-окон в минуте.

Сформируй краткий итог урока на русском языке:
1. Общая динамика урока.
2. В какие минуты было больше всего шума, когда учитель не говорил. Реагируй на такой шум жестче.
3. Примерно какую долю урока говорил учитель. Дай примерный процент.
4. Оцени дисциплину на уроке по шуму ореинтируйся на всё время занятия не только на начало. 
5. Краткий конспект по словам учителя, если teacher_transcript не пустой.
6. Что можно улучшить на следующем уроке.
7.Если в речи учителя будут имена детей оцени похвала эта или наоборот. Если имя упоминается просто так, напиши, что дети не отмечены
8.Если упомянутые дети есть - выдай их примерную оценку от учителя.

Не упоминай технические названия полей JSON.
Не придумывай факты, которых нет в JSON.
Пиши дружелюбно, кратко и полезно для учителя.
""".strip()

router = APIRouter(prefix="/lesson-report", tags=["lesson-report"])


class TimelineMinuteWindow(BaseModel):
    minute: int
    start_at: str
    end_at: str
    average_loudness_dbfs: float
    teacher_speaking_percent: float
    teacher_transcript: str = ""
    samples_count: int


class LessonReportCreate(BaseModel):
    timeline: list[TimelineMinuteWindow] = Field(default_factory=list)


class LessonReportOut(BaseModel):
    report: str
    raw_response: dict[str, Any] | None = None


def _yandex_gpt_configured() -> bool:
    settings = get_settings()
    return bool(settings.yandex_api_key and settings.yandex_folder_id)


def _headers(settings: Settings) -> dict[str, str]:
    return {
        "Authorization": f"Api-Key {settings.yandex_api_key}",
        "Content-Type": "application/json",
    }


def _http_error_detail(exc: BaseException, url: str) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            body = ""

        req_url = getattr(exc, "url", None) or url
        return f"POST {req_url} → HTTP {exc.code}: {body[:1000] or exc.reason}"

    if isinstance(exc, urllib.error.URLError):
        return f"POST {url} → {exc.reason}"

    return f"POST {url} → {exc}"


def _request_json(
    url: str,
    payload: dict[str, Any],
    settings: Settings,
    *,
    timeout: int = 120,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers=_headers(settings),
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _model_dump(item: BaseModel) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return item.dict()


def _build_user_input(timeline: list[TimelineMinuteWindow]) -> str:
    return (
        "JSON-таймлайн урока:\n"
        + json.dumps(
            [_model_dump(item) for item in timeline],
            ensure_ascii=False,
            indent=2,
        )
    )


def _lesson_report_request(
    settings: Settings,
    timeline: list[TimelineMinuteWindow],
) -> dict[str, Any]:
    payload = {
        "modelUri": f"gpt://{settings.yandex_folder_id}/yandexgpt-lite/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": "2000",
        },
        "messages": [
            {
                "role": "system",
                "text": YANDEX_LESSON_REPORT_PROMPT,
            },
            {
                "role": "user",
                "text": _build_user_input(timeline),
            },
        ],
    }

    return _request_json(YANDEX_COMPLETION_URL, payload, settings, timeout=120)


def _extract_report_text(response: dict[str, Any]) -> str:
    alternatives = (
        response.get("result", {})
        .get("alternatives", [])
    )

    texts: list[str] = []

    for alternative in alternatives:
        if not isinstance(alternative, dict):
            continue

        message = alternative.get("message")
        if not isinstance(message, dict):
            continue

        text = message.get("text")
        if text:
            texts.append(str(text).strip())

    return "\n".join(texts).strip()


def create_yandex_lesson_report(timeline: list[TimelineMinuteWindow]) -> LessonReportOut:
    if not _yandex_gpt_configured():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="YandexGPT не настроен: не заданы YANDEX_API_KEY или YANDEX_FOLDER_ID",
        )

    settings = get_settings()
    last_error = "неизвестная ошибка"

    for attempt in range(1, LESSON_REPORT_RETRY_ATTEMPTS + 1):
        logger.info(
            "YandexGPT lesson report: попытка %s/%s POST %s",
            attempt,
            LESSON_REPORT_RETRY_ATTEMPTS,
            YANDEX_COMPLETION_URL,
        )

        try:
            response = _lesson_report_request(settings, timeline)
            report = _extract_report_text(response)

            return LessonReportOut(
                report=report or "YandexGPT вернул пустой отчёт.",
                raw_response=response,
            )
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, KeyError, ValueError) as exc:
            last_error = _http_error_detail(exc, YANDEX_COMPLETION_URL)
            logger.warning(
                "YandexGPT lesson report: попытка %s/%s — %s",
                attempt,
                LESSON_REPORT_RETRY_ATTEMPTS,
                last_error,
            )

        if attempt < LESSON_REPORT_RETRY_ATTEMPTS:
            delay = LESSON_REPORT_RETRY_BASE_DELAY_SEC * (2 ** (attempt - 1))
            logger.info(
                "YandexGPT lesson report: повтор через %.1f с → POST %s",
                delay,
                YANDEX_COMPLETION_URL,
            )
            time.sleep(delay)

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"YandexGPT lesson report failed: {last_error}",
    )


@router.post("", response_model=LessonReportOut)
def create_lesson_report(payload: LessonReportCreate) -> LessonReportOut:
    if not payload.timeline:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timeline is empty",
        )

    return create_yandex_lesson_report(payload.timeline)
