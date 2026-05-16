from __future__ import annotations

import io
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.core.enums import NoiseSessionStatus, UserRole
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.noise import NoiseSample, NoiseSession, StudentNoiseStat
from app.models.school import StudentEnrollment
from app.models.user import User
from app.schemas.noise import (
    NoiseSessionCreate,
    NoiseSessionListResponse,
    NoiseSessionOut,
    NoiseSampleOut,
    StudentNoiseStatOut,
)
from app.services.storage import upload_file

router = APIRouter(prefix="/noise", tags=["noise"])


def _session_to_out(session: NoiseSession) -> NoiseSessionOut:
    return NoiseSessionOut(
        id=session.id,
        lesson_id=session.id,
        class_id=session.class_id,
        class_name=session.class_group.name,
        subject_name=session.subject.name,
        started_at=session.started_at,
        ended_at=session.ended_at,
        samples=[
            NoiseSampleOut(timestamp=s.recorded_at, level_db=s.level_db) for s in session.samples
        ],
        top_noisy_students=[
            StudentNoiseStatOut(
                student_id=st.student_id,
                student_name=st.student.full_name,
                avg_level_db=st.avg_level_db,
                peak_level_db=st.peak_level_db,
                incidents_count=st.incidents_count,
            )
            for st in session.student_stats
        ],
        summary=session.summary,
        status=session.status,
    )


def _load_session(db: Session, session_id: UUID) -> NoiseSession | None:
    return (
        db.query(NoiseSession)
        .options(
            joinedload(NoiseSession.class_group),
            joinedload(NoiseSession.subject),
            joinedload(NoiseSession.samples),
            joinedload(NoiseSession.student_stats).joinedload(StudentNoiseStat.student),
        )
        .filter(NoiseSession.id == session_id)
        .first()
    )


@router.post("/sessions", response_model=NoiseSessionOut, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: NoiseSessionCreate,
    user: User = Depends(require_roles(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> NoiseSessionOut:
    session = NoiseSession(
        teacher_id=user.id,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        status=NoiseSessionStatus.recording,
    )
    db.add(session)
    db.commit()
    loaded = _load_session(db, session.id)
    assert loaded is not None
    return _session_to_out(loaded)


@router.post("/sessions/{session_id}/stop", response_model=NoiseSessionOut)
async def stop_session(
    session_id: UUID,
    audio: UploadFile | None = File(None),
    user: User = Depends(require_roles(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> NoiseSessionOut:
    session = db.get(NoiseSession, session_id)
    if session is None or session.teacher_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if audio and audio.filename:
        data = await audio.read()
        settings = get_settings()
        content_type = audio.content_type or "audio/webm"
        session.audio_key = upload_file(
            settings.minio_bucket_lesson_media,
            io.BytesIO(data),
            content_type,
            prefix=f"noise/{session_id}/",
        )

    session.ended_at = datetime.now(timezone.utc)
    session.status = NoiseSessionStatus.processing
    db.commit()

    # Заглушка: сразу «готовый» отчёт
    session.status = NoiseSessionStatus.ready
    session.summary = (
        "Урок завершён. Средний уровень шума в норме. "
        "Рекомендуется обратить внимание на активность в задних рядах."
    )
    students = (
        db.query(StudentEnrollment)
        .options(joinedload(StudentEnrollment.student))
        .filter(StudentEnrollment.class_id == session.class_id)
        .limit(3)
        .all()
    )
    for i, enr in enumerate(students):
        db.add(
            StudentNoiseStat(
                session_id=session.id,
                student_id=enr.student_id,
                avg_level_db=55.0 + i * 5,
                peak_level_db=75.0 + i * 3,
                incidents_count=2 + i,
            )
        )
    db.add(
        NoiseSample(
            session_id=session.id,
            recorded_at=datetime.now(timezone.utc),
            level_db=48.5,
        )
    )
    db.commit()

    loaded = _load_session(db, session_id)
    assert loaded is not None
    return _session_to_out(loaded)


@router.get("/sessions/{session_id}/report", response_model=NoiseSessionOut)
def get_report(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoiseSessionOut:
    session = _load_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if user.role == UserRole.teacher and session.teacher_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return _session_to_out(session)


@router.get("/lessons", response_model=NoiseSessionListResponse)
def list_lessons(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NoiseSessionListResponse:
    q = db.query(NoiseSession).options(
        joinedload(NoiseSession.class_group),
        joinedload(NoiseSession.subject),
        joinedload(NoiseSession.samples),
        joinedload(NoiseSession.student_stats).joinedload(StudentNoiseStat.student),
    )
    if user.role == UserRole.teacher:
        q = q.filter(NoiseSession.teacher_id == user.id)
    elif user.role != UserRole.director:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    sessions = q.order_by(NoiseSession.started_at.desc()).all()
    return NoiseSessionListResponse(items=[_session_to_out(s) for s in sessions])
