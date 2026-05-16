from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import HomeworkStatus


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


class HomeworkListResponse(BaseModel):
    items: list[HomeworkOut]


class GradeUpdateRequest(BaseModel):
    grade: float = Field(ge=2, le=5)
