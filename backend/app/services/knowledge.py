from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.homework import HomeworkSubmission
from app.models.knowledge import SubjectKnowledgeFact

MAX_FACTS_IN_PROMPT = 20


def get_facts_for_review(
    db: Session,
    subject_id: UUID,
    grade: Optional[int] = None,
) -> list[SubjectKnowledgeFact]:
    query = db.query(SubjectKnowledgeFact).filter(SubjectKnowledgeFact.subject_id == subject_id)

    if grade is not None:
        query = query.filter(
            or_(
                SubjectKnowledgeFact.grade_from.is_(None),
                SubjectKnowledgeFact.grade_from <= grade,
            ),
            or_(
                SubjectKnowledgeFact.grade_to.is_(None),
                SubjectKnowledgeFact.grade_to >= grade,
            ),
        )

    return query.order_by(SubjectKnowledgeFact.sort_order).limit(MAX_FACTS_IN_PROMPT).all()


def format_knowledge_context(subject_name: str, facts: list[SubjectKnowledgeFact], grade: Optional[int]) -> str:
    if not facts:
        return f"Справочные факты по предмету «{subject_name}» не найдены."

    grade_label = f" ({grade} класс)" if grade is not None else ""
    lines = [f"Справочные факты по предмету «{subject_name}»{grade_label}:"]
    for fact in facts:
        topic = f"[{fact.topic}] " if fact.topic else ""
        lines.append(f"- {topic}{fact.content}")
    return "\n".join(lines)


def build_homework_review_prompt(
    submission: HomeworkSubmission,
    subject_name: str,
    class_grade: Optional[int],
    facts: list[SubjectKnowledgeFact],
    image_url: Optional[str] = None,
) -> str:
    knowledge_block = format_knowledge_context(subject_name, facts, class_grade)
    image_line = f"\nФото работы: {image_url}" if image_url else "\nФото работы приложено."

    return f"""Ты — помощник учителя. Проверь домашнюю работу ученика по предмету «{subject_name}».
Шкала оценок: от 2 до 5 (дробные значения допустимы, например 4.5).

{knowledge_block}

Инструкция:
1. Сверь решение на фото со справочными фактами выше.
2. Укажи конкретные ошибки или подтверди правильность.
3. Поставь оценку от 2 до 5 и краткий комментарий на русском языке.
{image_line}
ID работы: {submission.id}
"""
