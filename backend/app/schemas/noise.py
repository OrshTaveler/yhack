from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.enums import NoiseSessionStatus


class NoiseSampleOut(BaseModel):
    timestamp: datetime
    level_db: float


class StudentNoiseStatOut(BaseModel):
    student_id: UUID
    student_name: str
    avg_level_db: float
    peak_level_db: float
    incidents_count: int


class NoiseSessionCreate(BaseModel):
    class_id: UUID
    subject_id: UUID


class NoiseSessionOut(BaseModel):
    id: UUID
    lesson_id: UUID
    class_id: UUID
    class_name: str
    subject_name: str
    started_at: datetime
    ended_at: datetime | None = None
    samples: list[NoiseSampleOut] = []
    top_noisy_students: list[StudentNoiseStatOut] = []
    summary: str | None = None
    status: NoiseSessionStatus


class NoiseSessionListResponse(BaseModel):
    items: list[NoiseSessionOut]
