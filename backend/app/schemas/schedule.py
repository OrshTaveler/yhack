from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ScheduleSlotOut(BaseModel):
    id: UUID
    day_of_week: int
    period: int
    subject_id: UUID
    subject_name: str
    class_id: UUID
    class_name: str
    teacher_id: UUID | None = None
    room: str | None = None

    model_config = {"from_attributes": True}


class ScheduleResponse(BaseModel):
    slots: list[ScheduleSlotOut]


class ClassInput(BaseModel):
    name: str
    grade: int = Field(ge=1, le=11)


class SubjectHoursInput(BaseModel):
    subject_name: str
    hours_per_week: int = Field(ge=1, le=40)


class ScheduleGenerateRequest(BaseModel):
    classes: list[ClassInput]
    subjects: list[SubjectHoursInput]
    periods_per_day: int = Field(default=6, ge=1, le=10)
    days_per_week: int = Field(default=5, ge=1, le=7)
