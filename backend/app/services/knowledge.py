from __future__ import annotations

from typing import Optional

from app.models.homework import HomeworkSubmission


def format_chunks_context(subject_name: str, chunks: list[str], grade: Optional[int]) -> str:
    if not chunks:
        return f"Справочные факты по предмету «{subject_name}» не найдены."

    grade_label = f" ({grade} класс)" if grade is not None else ""
    lines = [f"Релевантные факты из базы знаний «{subject_name}»{grade_label}:"]
    for chunk in chunks:
        lines.append(f"- {chunk.strip()}")
    return "\n".join(lines)


def build_homework_review_prompt(
    submission: HomeworkSubmission,
    subject_name: str,
    class_grade: Optional[int],
    knowledge_context: str,
    ocr_text: Optional[str] = None,
    text_unique: Optional[float] = None,
    ai_probability: Optional[float] = None,
    image_url: Optional[str] = None,
) -> str:
    ocr_block = ocr_text.strip() if ocr_text and ocr_text.strip() else "(текст не распознан)"
    plag_line = f"Уникальность текста (антиплагиат): {text_unique:.0f}%." if text_unique is not None else ""
    ai_line = (
        f"Вероятность AI-генерации текста: {ai_probability:.0f}%."
        if ai_probability is not None
        else ""
    )
    image_line = f"\nФото работы: {image_url}" if image_url else ""

    return f"""Ты — помощник учителя. Проанализируй домашнюю работу ученика по предмету «{subject_name}».
Оценку НЕ ставь — только подскажи учителю, на что обратить внимание при проверке.

{knowledge_context}

Текст работы (OCR):
{ocr_block}

{plag_line}
{ai_line}

Инструкция:
1. Сверь решение со справочными фактами выше.
2. Найди проблемные места: ошибки, неточности, пропуски, сомнительные рассуждения.
3. Для каждого замечания укажи фрагмент решения (цитату из OCR или описание места).
4. Кратко отметь сильные стороны, если они есть.
5. Не предлагай итоговый балл — оценку выставит учитель.
{image_line}
ID работы: {submission.id}
"""
