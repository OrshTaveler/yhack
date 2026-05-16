from __future__ import annotations

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ClassSubjectHours(Base):
    __tablename__ = "class_subject_hours"
    __table_args__ = (UniqueConstraint("class_id", "subject_id", name="uq_class_subject_hours"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    hours_per_week: Mapped[int] = mapped_column(Integer, nullable=False)

    class_group: Mapped["ClassGroup"] = relationship(back_populates="subject_hours")
    subject: Mapped["Subject"] = relationship(back_populates="subject_hours")


class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"
    __table_args__ = (
        UniqueConstraint("class_id", "day_of_week", "period", name="uq_schedule_slot"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon .. 4=Fri
    period: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..6
    room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    class_group: Mapped["ClassGroup"] = relationship(back_populates="schedule_slots")
    subject: Mapped["Subject"] = relationship(back_populates="schedule_slots")
    teacher: Mapped[Optional["User"]] = relationship()
