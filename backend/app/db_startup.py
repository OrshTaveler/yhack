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
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE class_groups "
                "ADD COLUMN IF NOT EXISTS students_count INTEGER NOT NULL DEFAULT 25"
            )
        )
