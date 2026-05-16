"""Заглушка ИИ-проверки домашних работ. Замените на вызов LLM/vision API."""

import random

from app.core.enums import HomeworkStatus
from app.models.homework import HomeworkSubmission


def run_ai_review(submission: HomeworkSubmission) -> None:
    submission.ai_grade = round(random.uniform(3.0, 5.0), 1)
    submission.ai_comment = "Автоматическая проверка: работа просмотрена, замечания минимальны."
    submission.status = HomeworkStatus.ai_reviewed
