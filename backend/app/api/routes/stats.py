from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.enums import HomeworkStatus, UserRole
from app.database import get_db
from app.dependencies import require_roles
from app.models.homework import HomeworkSubmission
from app.models.school import ClassGroup, ClassTeacherAssignment, StudentEnrollment
from app.models.user import User
from app.schemas.stats import (
    ClassGradesResponse,
    ClassOverviewOut,
    StudentGradeStatOut,
    TeacherStatsResponse,
)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/teacher", response_model=TeacherStatsResponse)
def teacher_overview(
    user: User = Depends(require_roles(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> TeacherStatsResponse:
    assignments = (
        db.query(ClassTeacherAssignment)
        .filter(ClassTeacherAssignment.teacher_id == user.id)
        .all()
    )
    class_ids = [a.class_id for a in assignments]
    classes_out: list[ClassOverviewOut] = []
    total_grade = 0.0
    grade_count = 0
    pending_total = 0

    for class_id in class_ids:
        cg = db.get(ClassGroup, class_id)
        if cg is None:
            continue
        enrolled = (
            db.query(StudentEnrollment).filter(StudentEnrollment.class_id == class_id).count()
        )
        students_count = cg.students_count if cg else enrolled
        pending = (
            db.query(HomeworkSubmission)
            .filter(
                HomeworkSubmission.class_id == class_id,
                HomeworkSubmission.status != HomeworkStatus.teacher_reviewed,
            )
            .count()
        )
        avg_row = (
            db.query(func.avg(HomeworkSubmission.teacher_grade))
            .filter(
                HomeworkSubmission.class_id == class_id,
                HomeworkSubmission.teacher_grade.isnot(None),
            )
            .scalar()
        )
        avg = float(avg_row) if avg_row else 0.0
        if avg_row:
            total_grade += avg
            grade_count += 1
        pending_total += pending
        classes_out.append(
            ClassOverviewOut(
                class_id=cg.id,
                class_name=cg.name,
                students_count=students_count,
                average_grade=round(avg, 2),
                pending_homeworks=pending,
            )
        )

    overall_avg = round(total_grade / grade_count, 2) if grade_count else 0.0
    return TeacherStatsResponse(
        pending_homeworks=pending_total,
        classes_count=len(class_ids),
        average_grade=overall_avg,
        classes=classes_out,
    )


@router.get("/class/{class_id}/grades", response_model=ClassGradesResponse)
def class_grades(
    class_id: UUID,
    user: User = Depends(require_roles(UserRole.teacher, UserRole.director)),
    db: Session = Depends(get_db),
) -> ClassGradesResponse:
    if user.role == UserRole.teacher:
        assigned = (
            db.query(ClassTeacherAssignment)
            .filter(
                ClassTeacherAssignment.class_id == class_id,
                ClassTeacherAssignment.teacher_id == user.id,
            )
            .first()
        )
        if assigned is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    enrollments = (
        db.query(StudentEnrollment)
        .filter(StudentEnrollment.class_id == class_id)
        .all()
    )
    items: list[StudentGradeStatOut] = []
    for enr in enrollments:
        student = db.get(User, enr.student_id)
        if student is None:
            continue
        rows = (
            db.query(HomeworkSubmission)
            .options(joinedload(HomeworkSubmission.subject))
            .filter(HomeworkSubmission.student_id == student.id)
            .all()
        )
        if not rows:
            continue
        grades = [r.teacher_grade or r.ai_grade for r in rows if (r.teacher_grade or r.ai_grade)]
        if not grades:
            continue
        subject = rows[0].subject
        items.append(
            StudentGradeStatOut(
                student_id=student.id,
                student_name=student.full_name,
                subject_id=rows[0].subject_id,
                subject_name=subject.name if subject else "—",
                average_grade=round(sum(grades) / len(grades), 2),
                works_count=len(rows),
            )
        )
    return ClassGradesResponse(items=items)
