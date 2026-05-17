#!/usr/bin/env python3
"""Собирает JSONL-файлы с чанками из app/data/subject_knowledge.py.

Выход:
  - knowledge_prechunked.jsonl — для консоли AI Studio («своё разбиение», JSON Line)
  - knowledge_chunks.jsonl     — тот же контент, поле text (для скриптов/отладки)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.data.subject_knowledge import KNOWLEDGE_BY_SUBJECT  # noqa: E402

DIR = Path(__file__).resolve().parent
OUTPUT_PRECHUNKED = DIR / "knowledge_prechunked.jsonl"
OUTPUT_CHUNKS = DIR / "knowledge_chunks.jsonl"

MAX_CHUNK_CHARS = 8000  # лимит Yandex AI Search на один чанк


def _grade_label(grade_from: Optional[int], grade_to: Optional[int]) -> str:
    if grade_from is not None and grade_to is not None:
        return f"{grade_from}-{grade_to}"
    if grade_from is not None:
        return f"{grade_from}+"
    if grade_to is not None:
        return f"до {grade_to}"
    return "все классы"


def _chunk_id(subject: str, topic: Optional[str], sort_order: int) -> str:
    raw = f"{subject}|{topic or 'general'}|{sort_order}".encode("utf-8")
    return "k_" + hashlib.sha256(raw).hexdigest()[:12]


def _chunk_body(
    subject: str,
    topic: Optional[str],
    fact_content: str,
    grade_from: Optional[int],
    grade_to: Optional[int],
) -> str:
    topic_label = topic or "общее"
    grade_label = _grade_label(grade_from, grade_to)
    return (
        f"Предмет: {subject}. Тема: {topic_label}. Класс: {grade_label}.\n\n"
        f"{fact_content}"
    )


def _metadata(
    subject: str,
    topic: Optional[str],
    grade_from: Optional[int],
    grade_to: Optional[int],
    sort_order: int,
    chunk_id: str,
) -> dict[str, Any]:
    return {
        "subject": subject,
        "topic": topic or "общее",
        "grade_from": grade_from,
        "grade_to": grade_to,
        "grade_label": _grade_label(grade_from, grade_to),
        "sort_order": sort_order,
        "chunk_id": chunk_id,
        "source": "subject_knowledge",
    }


def _prechunked_record(
    subject: str,
    topic: Optional[str],
    fact_content: str,
    grade_from: Optional[int],
    grade_to: Optional[int],
    sort_order: int,
) -> dict[str, Any]:
    """Формат для консоли: «индекс на основе вашего разбиения» (JSON Line)."""
    chunk_id = _chunk_id(subject, topic, sort_order)
    body = _chunk_body(subject, topic, fact_content, grade_from, grade_to)
    if len(body) > MAX_CHUNK_CHARS:
        body = body[: MAX_CHUNK_CHARS - 1] + "…"
    return {
        "content": body,
        "metadata": _metadata(subject, topic, grade_from, grade_to, sort_order, chunk_id),
    }


def _chunks_record(
    subject: str,
    topic: Optional[str],
    fact_content: str,
    grade_from: Optional[int],
    grade_to: Optional[int],
    sort_order: int,
) -> dict[str, Any]:
    """Внутренний формат (поле text) — совместим с отладкой и API file_search."""
    chunk_id = _chunk_id(subject, topic, sort_order)
    body = _chunk_body(subject, topic, fact_content, grade_from, grade_to)
    return {
        "text": body,
        "metadata": _metadata(subject, topic, grade_from, grade_to, sort_order, chunk_id),
    }


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )


def build_jsonl() -> tuple[int, int]:
    prechunked: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    for subject_name, facts in KNOWLEDGE_BY_SUBJECT.items():
        for topic, content, grade_from, grade_to, sort_order in facts:
            prechunked.append(
                _prechunked_record(subject_name, topic, content, grade_from, grade_to, sort_order)
            )
            chunks.append(
                _chunks_record(subject_name, topic, content, grade_from, grade_to, sort_order)
            )
    _write_jsonl(OUTPUT_PRECHUNKED, prechunked)
    _write_jsonl(OUTPUT_CHUNKS, chunks)
    return len(prechunked), len(chunks)


if __name__ == "__main__":
    n_pre, n_chunks = build_jsonl()
    print(f"Предразмеченные чанки (консоль): {n_pre} → {OUTPUT_PRECHUNKED}")
    print(f"Чанки (text):                {n_chunks} → {OUTPUT_CHUNKS}")
