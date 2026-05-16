from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.enums import HomeworkStatus, UserRole
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.homework import HomeworkSubmission
from app.models.school import ClassTeacherAssignment, StudentEnrollment
from app.models.user import User
from app.schemas.profile import (
    ProgressPointOut,
    RecentWorkOut,
    StudentProfileOut,
    SubjectProgressOut,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _effective_grade(work: HomeworkSubmission) -> float | None:
    """Оценка учителя приоритетнее оценки ИИ."""
    if work.teacher_grade is not None:
        return work.teacher_grade
    return work.ai_grade


def _level_for(avg: float) -> str:
    """Уровень владения предметом по среднему баллу."""
    if avg < 3.5:
        return "weak"
    if avg < 4.3:
        return "normal"
    return "strong"


def _build_profile(db: Session, student: User) -> StudentProfileOut:
    """Собирает агрегированный профиль ученика из домашних работ."""
    enrollment = (
        db.query(StudentEnrollment)
        .options(joinedload(StudentEnrollment.class_group))
        .filter(StudentEnrollment.student_id == student.id)
        .first()
    )
    class_name = enrollment.class_group.name if enrollment else None

    works = (
        db.query(HomeworkSubmission)
        .options(joinedload(HomeworkSubmission.subject))
        .filter(HomeworkSubmission.student_id == student.id)
        .order_by(HomeworkSubmission.submitted_at.asc())
        .all()
    )

    total_works = len(works)
    graded_works = [w for w in works if _effective_grade(w) is not None]
    checked_works = len(graded_works)

    average_grade = (
        round(sum(_effective_grade(w) for w in graded_works) / checked_works, 2)
        if checked_works
        else 0.0
    )

    # Группировка по предметам
    by_subject: dict[UUID, list[HomeworkSubmission]] = {}
    for w in works:
        by_subject.setdefault(w.subject_id, []).append(w)

    subjects: list[SubjectProgressOut] = []
    for subject_id, subject_works in by_subject.items():
        graded = [w for w in subject_works if _effective_grade(w) is not None]
        if not graded:
            continue
        grades = [_effective_grade(w) for w in graded]
        avg = round(sum(grades) / len(grades), 2)
        subject_name = graded[0].subject.name if graded[0].subject else "—"
        subjects.append(
            SubjectProgressOut(
                subject_id=subject_id,
                subject_name=subject_name,
                average_grade=avg,
                works_count=len(subject_works),
                last_grade=_effective_grade(graded[-1]),
                level=_level_for(avg),
            )
        )

    subjects.sort(key=lambda s: s.average_grade, reverse=True)
    best_subject = subjects[0].subject_name if subjects else None
    weak_subjects = [s.subject_name for s in subjects if s.level == "weak"]

    # График прогресса — все проверенные работы по времени
    progress_timeline = [
        ProgressPointOut(
            date=w.submitted_at,
            grade=_effective_grade(w),
            subject_name=w.subject.name if w.subject else "—",
        )
        for w in graded_works
    ]

    # Последние работы (свежие сверху)
    recent_works = [
        RecentWorkOut(
            id=w.id,
            subject_name=w.subject.name if w.subject else "—",
            submitted_at=w.submitted_at,
            grade=_effective_grade(w),
            status=w.status,
            ai_comment=w.ai_comment,
        )
        for w in reversed(works[-5:])
    ]

    return StudentProfileOut(
        student_id=student.id,
        student_name=student.full_name,
        class_name=class_name,
        total_works=total_works,
        checked_works=checked_works,
        average_grade=average_grade,
        best_subject=best_subject,
        weak_subjects=weak_subjects,
        subjects=subjects,
        progress_timeline=progress_timeline,
        recent_works=recent_works,
    )


@router.get("/me", response_model=StudentProfileOut)
def my_profile(
    user: User = Depends(require_roles(UserRole.student)),
    db: Session = Depends(get_db),
) -> StudentProfileOut:
    """Профиль текущего ученика."""
    return _build_profile(db, user)


@router.get("/student/{student_id}", response_model=StudentProfileOut)
def student_profile(
    student_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentProfileOut:
    """Профиль ученика для учителя/директора (связка ролей)."""
    if user.role == UserRole.student and user.id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    student = db.get(User, student_id)
    if student is None or student.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Учитель видит профиль только ученика из своего класса
    if user.role == UserRole.teacher:
        enrollment = (
            db.query(StudentEnrollment)
            .filter(StudentEnrollment.student_id == student_id)
            .first()
        )
        if enrollment is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        assigned = (
            db.query(ClassTeacherAssignment)
            .filter(
                ClassTeacherAssignment.class_id == enrollment.class_id,
                ClassTeacherAssignment.teacher_id == user.id,
            )
            .first()
        )
        if assigned is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return _build_profile(db, student)
