from __future__ import annotations

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import HomeworkStatus
from app.database import Base


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    file_key: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[HomeworkStatus] = mapped_column(
        Enum(HomeworkStatus, name="homework_status"),
        default=HomeworkStatus.pending,
        nullable=False,
    )
    ai_grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    teacher_grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Распознанный текст (Vision OCR)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Антиплагиат (text.ru)
    text_unique: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    plagiarism_sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # AI-детектор (YandexGPT)
    ai_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_detector_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    student: Mapped["User"] = relationship(
        back_populates="homework_submissions",
        foreign_keys=[student_id],
    )
    class_group: Mapped["ClassGroup"] = relationship()
    subject: Mapped["Subject"] = relationship()
