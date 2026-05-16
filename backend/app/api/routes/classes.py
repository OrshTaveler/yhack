from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.database import get_db
from app.dependencies import require_roles
from app.models.school import ClassGroup, ClassTeacherAssignment
from app.models.user import User
from app.schemas.classes import AssignTeacherRequest, ClassListResponse, ClassOut

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=ClassListResponse)
def list_classes(
    _: User = Depends(require_roles(UserRole.director, UserRole.teacher, UserRole.student)),
    db: Session = Depends(get_db),
) -> ClassListResponse:
    classes = db.query(ClassGroup).all()
    items: list[ClassOut] = []
    for cg in classes:
        assignment = (
            db.query(ClassTeacherAssignment)
            .filter(ClassTeacherAssignment.class_id == cg.id)
            .first()
        )
        teacher = db.get(User, assignment.teacher_id) if assignment else None
        items.append(
            ClassOut(
                id=cg.id,
                name=cg.name,
                grade=cg.grade,
                students_count=cg.students_count,
                teacher_id=teacher.id if teacher else None,
                teacher_name=teacher.full_name if teacher else None,
            )
        )
    return ClassListResponse(items=items)


@router.put("/{class_id}/teacher", response_model=ClassOut)
def assign_teacher(
    class_id: UUID,
    payload: AssignTeacherRequest,
    _: User = Depends(require_roles(UserRole.director)),
    db: Session = Depends(get_db),
) -> ClassOut:
    cg = db.get(ClassGroup, class_id)
    if cg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    teacher = db.get(User, payload.teacher_id)
    if teacher is None or teacher.role != UserRole.teacher:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid teacher")

    existing = (
        db.query(ClassTeacherAssignment)
        .filter(ClassTeacherAssignment.class_id == class_id)
        .first()
    )
    if existing:
        existing.teacher_id = payload.teacher_id
    else:
        db.add(ClassTeacherAssignment(class_id=class_id, teacher_id=payload.teacher_id))
    db.commit()

    return ClassOut(
        id=cg.id,
        name=cg.name,
        grade=cg.grade,
        students_count=cg.students_count,
        teacher_id=teacher.id,
        teacher_name=teacher.full_name,
    )
