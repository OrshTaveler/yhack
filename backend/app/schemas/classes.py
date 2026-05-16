from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class ClassOut(BaseModel):
    id: UUID
    name: str
    grade: int
    teacher_id: UUID | None = None
    teacher_name: str | None = None

    model_config = {"from_attributes": True}


class ClassListResponse(BaseModel):
    items: list[ClassOut]


class AssignTeacherRequest(BaseModel):
    teacher_id: UUID
