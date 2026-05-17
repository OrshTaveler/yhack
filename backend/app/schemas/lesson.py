from __future__ import annotations

from pydantic import BaseModel


class LessonAnalyzeRequest(BaseModel):
    transcript: str


class StudentMentionOut(BaseModel):
    name: str
    type: str  # praise | remark
    quote: str


class LessonReportOut(BaseModel):
    students: list[StudentMentionOut]
    summary: list[str]
    homework: str
    ok: bool
    note: str = ""
