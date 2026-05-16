from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.core.enums import UserRole


class UserListItem(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: UserRole


class UserListResponse(BaseModel):
    items: list[UserListItem]
