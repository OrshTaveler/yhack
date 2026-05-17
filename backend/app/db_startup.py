from __future__ import annotations

import logging
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import engine

logger = logging.getLogger(__name__)


def wait_for_db(max_attempts: int = 30, delay_sec: float = 1.0) -> None:
    """Ждёт готовности PostgreSQL (удобно после docker compose up)."""
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("PostgreSQL is ready")
            return
        except OperationalError as exc:
            last_error = exc
            logger.warning("DB not ready (attempt %s/%s): %s", attempt, max_attempts, exc)
            time.sleep(delay_sec)
    raise RuntimeError(
        "Не удалось подключиться к PostgreSQL. "
        "Проверьте docker compose и DATABASE_URL в .env (порт 5433)."
    ) from last_error


def ensure_schema_updates() -> None:
    """Добавляет новые колонки в существующую БД (без Alembic)."""
    # Skip for SQLite - it doesn't support IF NOT EXISTS in ALTER TABLE
    if "sqlite" in str(engine.url):
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE class_groups "
                "ADD COLUMN IF NOT EXISTS students_count INTEGER NOT NULL DEFAULT 25"
            )
        )
        conn.execute(
            text(
                "ALTER TABLE homework_submissions "
                "ADD COLUMN IF NOT EXISTS ai_prompt_snapshot TEXT"
            )
        )
        for col_sql in (
            "ALTER TABLE homework_submissions ADD COLUMN IF NOT EXISTS ocr_text TEXT",
            "ALTER TABLE homework_submissions ADD COLUMN IF NOT EXISTS text_unique DOUBLE PRECISION",
            "ALTER TABLE homework_submissions ADD COLUMN IF NOT EXISTS plagiarism_sources TEXT",
            "ALTER TABLE homework_submissions ADD COLUMN IF NOT EXISTS ai_probability DOUBLE PRECISION",
            "ALTER TABLE homework_submissions ADD COLUMN IF NOT EXISTS ai_detector_reason TEXT",
        ):
            conn.execute(text(col_sql))
