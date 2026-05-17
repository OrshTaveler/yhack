from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.school import Subject
from app.models.user import User
from app.schemas.subjects import SubjectListResponse, SubjectOut

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=SubjectListResponse)
def list_subjects(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubjectListResponse:
    subjects = db.query(Subject).order_by(Subject.name).all()
    return SubjectListResponse(items=[SubjectOut.model_validate(s) for s in subjects])
