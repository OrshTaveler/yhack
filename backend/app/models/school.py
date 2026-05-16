from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ClassGroup(Base):
    __tablename__ = "class_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    students_count: Mapped[int] = mapped_column(Integer, nullable=False, default=25)

    teacher_assignments: Mapped[list["ClassTeacherAssignment"]] = relationship(back_populates="class_group")
    enrollments: Mapped[list["StudentEnrollment"]] = relationship(back_populates="class_group")
    schedule_slots: Mapped[list["ScheduleSlot"]] = relationship(back_populates="class_group")
    subject_hours: Mapped[list["ClassSubjectHours"]] = relationship(back_populates="class_group")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    schedule_slots: Mapped[list["ScheduleSlot"]] = relationship(back_populates="subject")
    subject_hours: Mapped[list["ClassSubjectHours"]] = relationship(back_populates="subject")
    knowledge_facts: Mapped[list["SubjectKnowledgeFact"]] = relationship(
        back_populates="subject",
        order_by="SubjectKnowledgeFact.sort_order",
    )


class ClassTeacherAssignment(Base):
    __tablename__ = "class_teacher_assignments"
    __table_args__ = (UniqueConstraint("class_id", "teacher_id", name="uq_class_teacher"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    class_group: Mapped["ClassGroup"] = relationship(back_populates="teacher_assignments")
    teacher: Mapped["User"] = relationship()


class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"
    __table_args__ = (UniqueConstraint("student_id", "class_id", name="uq_student_class"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False)

    student: Mapped["User"] = relationship()
    class_group: Mapped["ClassGroup"] = relationship(back_populates="enrollments")
