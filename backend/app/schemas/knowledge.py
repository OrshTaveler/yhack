from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KnowledgeFactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_id: UUID
    topic: Optional[str] = None
    content: str
    grade_from: Optional[int] = None
    grade_to: Optional[int] = None
    sort_order: int


class KnowledgeFactListResponse(BaseModel):
    items: list[KnowledgeFactOut]
