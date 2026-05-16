from __future__ import annotations

import io
import json
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.core.enums import HomeworkStatus, UserRole
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.homework import HomeworkSubmission
from app.models.school import StudentEnrollment
from app.models.user import User
from app.schemas.homework import (
    GradeUpdateRequest,
    HomeworkListResponse,
    HomeworkOut,
    PlagiarismSource,
)
from app.services.homework_ai import run_homework_pipeline
from app.services.storage import get_presigned_url, upload_file

router = APIRouter(prefix="/homework", tags=["homework"])


def _homework_to_out(item: HomeworkSubmission) -> HomeworkOut:
    settings = get_settings()
    try:
        photo_url = get_presigned_url(settings.minio_bucket_homework, item.file_key)
    except Exception:  # noqa: BLE001 — демо-данные с фейковым ключом
        photo_url = ""

    sources: list[PlagiarismSource] = []
    if item.plagiarism_sources:
        try:
            sources = [PlagiarismSource(**s) for s in json.loads(item.plagiarism_sources)]
        except (json.JSONDecodeError, TypeError):
            sources = []

    return HomeworkOut(
        id=item.id,
        student_id=item.student_id,
        student_name=item.student.full_name,
        class_id=item.class_id,
        subject_id=item.subject_id,
        subject_name=item.subject.name,
        photo_url=photo_url,
        submitted_at=item.submitted_at,
        ai_grade=item.ai_grade,
        ai_comment=item.ai_comment,
        teacher_grade=item.teacher_grade,
        status=item.status,
        ocr_text=item.ocr_text,
        text_unique=item.text_unique,
        plagiarism_sources=sources,
        ai_probability=item.ai_probability,
        ai_detector_reason=item.ai_detector_reason,
    )


@router.get("/teacher", response_model=HomeworkListResponse)
def list_for_teacher(
    user: User = Depends(require_roles(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> HomeworkListResponse:
    from app.models.school import ClassTeacherAssignment

    class_ids = [
        a.class_id
        for a in db.query(ClassTeacherAssignment).filter(ClassTeacherAssignment.teacher_id == user.id).all()
    ]
    if not class_ids:
        return HomeworkListResponse(items=[])

    items = (
        db.query(HomeworkSubmission)
        .options(joinedload(HomeworkSubmission.student), joinedload(HomeworkSubmission.subject))
        .filter(HomeworkSubmission.class_id.in_(class_ids))
        .order_by(HomeworkSubmission.submitted_at.desc())
        .all()
    )
    return HomeworkListResponse(items=[_homework_to_out(i) for i in items])


@router.get("/my", response_model=HomeworkListResponse)
def list_my_homework(
    user: User = Depends(require_roles(UserRole.student)),
    db: Session = Depends(get_db),
) -> HomeworkListResponse:
    items = (
        db.query(HomeworkSubmission)
        .options(joinedload(HomeworkSubmission.student), joinedload(HomeworkSubmission.subject))
        .filter(HomeworkSubmission.student_id == user.id)
        .order_by(HomeworkSubmission.submitted_at.desc())
        .all()
    )
    return HomeworkListResponse(items=[_homework_to_out(i) for i in items])


@router.post("/upload", response_model=HomeworkOut, status_code=status.HTTP_201_CREATED)
async def upload_homework(
    background_tasks: BackgroundTasks,
    subject_id: UUID = Form(...),
    class_id: UUID | None = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(require_roles(UserRole.student)),
    db: Session = Depends(get_db),
) -> HomeworkOut:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only images are allowed")

    enrollment = (
        db.query(StudentEnrollment)
        .filter(StudentEnrollment.student_id == user.id)
        .first()
    )
    resolved_class_id = class_id or (enrollment.class_id if enrollment else None)
    if resolved_class_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="class_id required or enroll student in a class",
        )

    data = await file.read()
    settings = get_settings()
    key = upload_file(
        settings.minio_bucket_homework,
        io.BytesIO(data),
        file.content_type,
        prefix=f"{user.id}/",
    )

    submission = HomeworkSubmission(
        student_id=user.id,
        class_id=resolved_class_id,
        subject_id=subject_id,
        file_key=key,
        status=HomeworkStatus.pending,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Пайплайн проверки (OCR → антиплагиат → AI-детектор) — в фоне,
    # т.к. text.ru может проверять до минуты. Ответ ученику — сразу.
    background_tasks.add_task(run_homework_pipeline, submission.id)

    submission = (
        db.query(HomeworkSubmission)
        .options(joinedload(HomeworkSubmission.student), joinedload(HomeworkSubmission.subject))
        .filter(HomeworkSubmission.id == submission.id)
        .one()
    )
    return _homework_to_out(submission)


@router.patch("/{homework_id}/grade", response_model=HomeworkOut)
def confirm_grade(
    homework_id: UUID,
    payload: GradeUpdateRequest,
    user: User = Depends(require_roles(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> HomeworkOut:
    item = (
        db.query(HomeworkSubmission)
        .options(joinedload(HomeworkSubmission.student), joinedload(HomeworkSubmission.subject))
        .filter(HomeworkSubmission.id == homework_id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")

    item.teacher_grade = payload.grade
    item.status = HomeworkStatus.teacher_reviewed
    db.commit()
    db.refresh(item)
    return _homework_to_out(item)
