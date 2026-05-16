from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import HomeworkStatus


class PlagiarismSource(BaseModel):
    url: str | None = None
    plagiat: float | None = None


class HomeworkOut(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str
    class_id: UUID
    subject_id: UUID
    subject_name: str
    photo_url: str
    submitted_at: datetime
    ai_grade: float | None = None
    ai_comment: str | None = None
    teacher_grade: float | None = None
    status: HomeworkStatus

    # Результаты пайплайна проверки
    ocr_text: str | None = None
    text_unique: float | None = None
    plagiarism_sources: list[PlagiarismSource] = []
    ai_probability: float | None = None
    ai_detector_reason: str | None = None


class HomeworkListResponse(BaseModel):
    items: list[HomeworkOut]


class GradeUpdateRequest(BaseModel):
    grade: float = Field(ge=2, le=5)
