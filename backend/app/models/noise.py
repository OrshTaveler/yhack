from __future__ import annotations

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import NoiseSessionStatus
from app.database import Base


class NoiseSession(Base):
    __tablename__ = "noise_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[NoiseSessionStatus] = mapped_column(
        Enum(NoiseSessionStatus, name="noise_session_status"),
        default=NoiseSessionStatus.recording,
        nullable=False,
    )
    audio_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    teacher: Mapped["User"] = relationship(back_populates="noise_sessions")
    class_group: Mapped["ClassGroup"] = relationship()
    subject: Mapped["Subject"] = relationship()
    samples: Mapped[list["NoiseSample"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    student_stats: Mapped[list["StudentNoiseStat"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class NoiseSample(Base):
    __tablename__ = "noise_samples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("noise_sessions.id", ondelete="CASCADE"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    level_db: Mapped[float] = mapped_column(Float, nullable=False)

    session: Mapped["NoiseSession"] = relationship(back_populates="samples")


class StudentNoiseStat(Base):
    __tablename__ = "student_noise_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("noise_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    avg_level_db: Mapped[float] = mapped_column(Float, nullable=False)
    peak_level_db: Mapped[float] = mapped_column(Float, nullable=False)
    incidents_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    session: Mapped["NoiseSession"] = relationship(back_populates="student_stats")
    student: Mapped["User"] = relationship()
