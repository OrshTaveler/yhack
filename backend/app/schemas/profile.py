from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import HomeworkStatus

# Уровень владения предметом, вычисляется по среднему баллу
SubjectLevel = str  # "weak" | "normal" | "strong"


class SubjectProgressOut(BaseModel):
    """Сводка по одному предмету в профиле ученика."""

    subject_id: UUID
    subject_name: str
    average_grade: float
    works_count: int
    last_grade: float | None = None
    level: SubjectLevel  # weak / normal / strong


class ProgressPointOut(BaseModel):
    """Точка на графике прогресса (одна проверенная работа)."""

    date: datetime
    grade: float
    subject_name: str


class RecentWorkOut(BaseModel):
    """Последняя работа с оценкой и замечанием ИИ."""

    id: UUID
    subject_name: str
    submitted_at: datetime
    grade: float | None = None
    status: HomeworkStatus
    ai_comment: str | None = None


class StudentProfileOut(BaseModel):
    """Полный персональный профиль ученика."""

    student_id: UUID
    student_name: str
    class_name: str | None = None

    total_works: int
    checked_works: int
    average_grade: float

    best_subject: str | None = None
    weak_subjects: list[str]

    subjects: list[SubjectProgressOut]
    progress_timeline: list[ProgressPointOut]
    recent_works: list[RecentWorkOut]
