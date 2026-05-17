from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.enums import UserRole
from app.dependencies import require_roles
from app.models.user import User
from app.schemas.lesson import LessonAnalyzeRequest, LessonReportOut, StudentMentionOut
from app.services.lesson_analyzer import analyze_lesson

router = APIRouter(prefix="/lesson", tags=["lesson"])


@router.post("/analyze", response_model=LessonReportOut)
def analyze(
    payload: LessonAnalyzeRequest,
    user: User = Depends(require_roles(UserRole.teacher)),
) -> LessonReportOut:
    """Расшифровка урока → отчёт: упоминания учеников, тезисы, ДЗ."""
    report = analyze_lesson(payload.transcript)
    return LessonReportOut(
        students=[
            StudentMentionOut(name=s.name, type=s.type, quote=s.quote)
            for s in report.students
        ],
        summary=report.summary,
        homework=report.homework,
        ok=report.ok,
        note=report.note,
    )
