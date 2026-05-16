from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.school import Subject
from app.models.user import User
from app.schemas.knowledge import KnowledgeFactListResponse, KnowledgeFactOut
from app.schemas.subjects import SubjectListResponse, SubjectOut
from app.services.knowledge import get_facts_for_review

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=SubjectListResponse)
def list_subjects(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubjectListResponse:
    subjects = db.query(Subject).order_by(Subject.name).all()
    return SubjectListResponse(items=[SubjectOut.model_validate(s) for s in subjects])


@router.get("/{subject_id}/knowledge", response_model=KnowledgeFactListResponse)
def list_subject_knowledge(
    subject_id: UUID,
    _: User = Depends(require_roles(UserRole.director, UserRole.teacher)),
    db: Session = Depends(get_db),
) -> KnowledgeFactListResponse:
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    facts = get_facts_for_review(db, subject_id, grade=None)
    return KnowledgeFactListResponse(items=[KnowledgeFactOut.model_validate(f) for f in facts])
