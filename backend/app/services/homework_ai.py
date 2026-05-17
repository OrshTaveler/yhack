"""Оркестратор проверки домашней работы.

Пайплайн (запускается в фоне после загрузки фото):
    1. Vision OCR           — фото → печатный текст
    2. text.ru              — антиплагиат
    3. YandexGPT            — детекция AI-генерации
    4. База знаний          — Yandex AI Search (с ретраями)
    5. YandexGPT            — замечания для учителя (без оценки)
    6. Сохранение в БД, статус → ai_reviewed
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional
from uuid import UUID

DEBUG_LOG_PATH = "/Users/nozhegoff/University/hackaton/.cursor/debug-28fa66.log"

from app.config import get_settings
from app.core.enums import HomeworkStatus
from app.database import SessionLocal
from app.models.homework import HomeworkSubmission
from app.models.school import ClassGroup, Subject
from app.services import ai_detector, ai_search, ocr, plagiarism
from app.services.homework_grader import review_homework
from app.services.storage import download_file, get_presigned_url

logger = logging.getLogger(__name__)


# #region agent log
def _agent_log(hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
    try:
        payload = {
            "sessionId": "28fa66",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


# #endregion


def _build_comment(
    review_comment: str,
    review_ok: bool,
    unique: float,
    ai_prob: float,
    knowledge_source: str,
) -> str:
    parts: list[str] = []
    if review_ok and review_comment:
        parts.append(f"Замечания для учителя: {review_comment}")
    elif review_comment:
        parts.append(review_comment)
    parts.append(f"Антиплагиат: {plagiarism.verdict(unique)} ({unique:.0f}% уникальности).")
    if ai_prob >= 70:
        parts.append(f"Высокая вероятность AI-генерации ({ai_prob:.0f}%).")
    elif ai_prob >= 30:
        parts.append(f"Возможна AI-генерация ({ai_prob:.0f}%).")
    else:
        parts.append("Текст похож на самостоятельную работу.")
    parts.append(f"База знаний: {knowledge_source}.")
    return " ".join(parts)


def run_homework_pipeline(submission_id: UUID) -> None:
    """Фоновая задача: полный пайплайн проверки одной работы."""
    db = SessionLocal()
    # #region agent log
    _agent_log(
        "H1",
        "homework_ai.py:run_homework_pipeline:start",
        "pipeline started",
        {"submission_id": str(submission_id)},
    )
    # #endregion
    try:
        sub = db.get(HomeworkSubmission, submission_id)
        if sub is None:
            logger.warning("Пайплайн: работа %s не найдена", submission_id)
            return

        settings = get_settings()
        subject = db.get(Subject, sub.subject_id)
        class_group = db.get(ClassGroup, sub.class_id)
        subject_name = subject.name if subject else "Неизвестный предмет"
        class_grade = class_group.grade if class_group else None

        # ── Шаг 1: OCR ──────────────────────────────
        try:
            image_bytes = download_file(settings.minio_bucket_homework, sub.file_key)
            logger.info(
                "Пайплайн %s: скачано фото %s (%d байт)",
                submission_id,
                sub.file_key,
                len(image_bytes),
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Пайплайн: не скачал файл %s (%s)", sub.file_key, e)
            image_bytes = b""

        ocr_text = ocr.recognize(image_bytes) if image_bytes else ""
        sub.ocr_text = ocr_text
        if ocr_text.strip():
            logger.info(
                "Пайплайн %s: OCR-текст (%d симв.)\n---\n%s\n---",
                submission_id,
                len(ocr_text),
                ocr_text if len(ocr_text) <= 4000 else f"{ocr_text[:4000]}…",
            )
        else:
            logger.warning("Пайплайн %s: OCR не распознал текст (пусто)", submission_id)

        # ── Шаг 2: антиплагиат ──────────────────────
        plag = plagiarism.check(ocr_text)
        sub.text_unique = plag.unique
        sub.plagiarism_sources = json.dumps(plag.sources, ensure_ascii=False)

        # ── Шаг 3: AI-детектор ──────────────────────
        ai = ai_detector.detect(ocr_text)
        sub.ai_probability = ai.probability
        sub.ai_detector_reason = ai.reason

        # ── Шаг 4: база знаний ──────────────────────
        retrieval = ai_search.retrieve_context(
            query=ocr_text or "",
            subject_name=subject_name,
            grade=class_grade,
        )
        # #region agent log
        _agent_log(
            "H5",
            "homework_ai.py:retrieve_context",
            "knowledge retrieval done",
            {
                "submission_id": str(submission_id),
                "source": retrieval.source,
                "chunks": len(retrieval.chunks),
                "context_len": len(retrieval.context or ""),
            },
        )
        # #endregion

        image_url: Optional[str] = None
        try:
            image_url = get_presigned_url(settings.minio_bucket_homework, sub.file_key)
        except Exception:  # noqa: BLE001
            pass

        # ── Шаг 5: замечания для учителя (без оценки) ─
        review = review_homework(
            sub,
            subject_name,
            class_grade,
            retrieval.context,
            ocr_text=ocr_text,
            text_unique=plag.unique,
            ai_probability=ai.probability,
            image_url=image_url,
        )
        sub.ai_prompt_snapshot = review.prompt
        # #region agent log
        _agent_log(
            "H3",
            "homework_ai.py:review_homework",
            "review result",
            {
                "submission_id": str(submission_id),
                "review_ok": review.ok,
                "comment_len": len(review.comment or ""),
                "comment_preview": (review.comment or "")[:120],
            },
        )
        # #endregion

        # ── Шаг 6: финальный комментарий ────────────
        unique_val = plag.unique if plag.unique is not None else 0.0
        ai_prob = ai.probability if ai.probability is not None else 0.0
        sub.ai_comment = _build_comment(
            review.comment,
            review.ok,
            unique_val,
            ai_prob,
            retrieval.source,
        )
        sub.status = HomeworkStatus.ai_reviewed
        db.commit()
        # #region agent log
        _agent_log(
            "H2",
            "homework_ai.py:run_homework_pipeline:committed",
            "pipeline committed",
            {
                "submission_id": str(submission_id),
                "status": sub.status.value,
                "ai_comment_len": len(sub.ai_comment or ""),
                "ai_comment_is_null": sub.ai_comment is None,
                "ai_comment_preview": (sub.ai_comment or "")[:200],
            },
        )
        # #endregion
        logger.info("Пайплайн завершён для работы %s (БЗ: %s)", submission_id, retrieval.source)
    except Exception as e:  # noqa: BLE001
        # #region agent log
        _agent_log(
            "H2",
            "homework_ai.py:run_homework_pipeline:exception",
            "pipeline failed",
            {"submission_id": str(submission_id), "error": str(e)},
        )
        # #endregion
        logger.exception("Пайплайн упал для %s: %s", submission_id, e)
        db.rollback()
    finally:
        db.close()
