from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class ClassOverviewOut(BaseModel):
    class_id: UUID
    class_name: str
    students_count: int
    average_grade: float
    pending_homeworks: int


class TeacherStatsResponse(BaseModel):
    pending_homeworks: int
    classes_count: int
    average_grade: float
    classes: list[ClassOverviewOut]


class StudentGradeStatOut(BaseModel):
    student_id: UUID
    student_name: str
    subject_id: UUID
    subject_name: str
    average_grade: float
    works_count: int


class ClassGradesResponse(BaseModel):
    items: list[StudentGradeStatOut]
