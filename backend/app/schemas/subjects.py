from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class SubjectOut(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class SubjectListResponse(BaseModel):
    items: list[SubjectOut]
