"""Оркестратор проверки домашней работы.

Пайплайн (запускается в фоне после загрузки фото):
    1. Vision OCR        — фото → печатный текст
    2. text.ru           — проверка на списывание (антиплагиат)
    3. YandexGPT         — детекция AI-генерации
    4. Сохранение результатов в БД, статус → ai_reviewed
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from app.config import get_settings
from app.core.enums import HomeworkStatus
from app.database import SessionLocal
from app.models.homework import HomeworkSubmission
from app.services import ai_detector, ocr, plagiarism
from app.services.storage import download_file

logger = logging.getLogger(__name__)


def _build_comment(unique: float, ai_prob: float) -> str:
    """Краткая сводка по результатам проверки."""
    parts = [f"Антиплагиат: {plagiarism.verdict(unique)} ({unique:.0f}% уникальности)."]
    if ai_prob >= 70:
        parts.append(f"⚠ Высокая вероятность AI-генерации ({ai_prob:.0f}%).")
    elif ai_prob >= 30:
        parts.append(f"Возможна AI-генерация ({ai_prob:.0f}%).")
    else:
        parts.append("Похоже на самостоятельную работу.")
    return " ".join(parts)


def run_homework_pipeline(submission_id: UUID) -> None:
    """Фоновая задача: полный пайплайн проверки одной работы."""
    db = SessionLocal()
    try:
        sub = db.get(HomeworkSubmission, submission_id)
        if sub is None:
            logger.warning("Пайплайн: работа %s не найдена", submission_id)
            return

        settings = get_settings()

        # ── Шаг 1: OCR ──────────────────────────────
        try:
            image_bytes = download_file(settings.minio_bucket_homework, sub.file_key)
        except Exception as e:  # noqa: BLE001 — файл мог не загрузиться
            logger.warning("Пайплайн: не скачал файл %s (%s)", sub.file_key, e)
            image_bytes = b""

        ocr_text = ocr.recognize(image_bytes) if image_bytes else ocr.recognize(b"")
        sub.ocr_text = ocr_text

        # ── Шаг 2: антиплагиат ──────────────────────
        plag = plagiarism.check(ocr_text)
        sub.text_unique = plag.unique
        sub.plagiarism_sources = json.dumps(plag.sources, ensure_ascii=False)

        # ── Шаг 3: AI-детектор ──────────────────────
        ai = ai_detector.detect(ocr_text)
        sub.ai_probability = ai.probability
        sub.ai_detector_reason = ai.reason

        # ── Шаг 4: финализация ──────────────────────
        sub.ai_comment = _build_comment(plag.unique, ai.probability)
        sub.status = HomeworkStatus.ai_reviewed
        db.commit()
        logger.info("Пайплайн завершён для работы %s", submission_id)
    except Exception as e:  # noqa: BLE001 — фон не должен падать молча
        logger.exception("Пайплайн упал для %s: %s", submission_id, e)
        db.rollback()
    finally:
        db.close()
