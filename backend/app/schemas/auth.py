from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import UserRole


class UserPublic(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: UserRole

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.student


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class MessageResponse(BaseModel):
    message: str
