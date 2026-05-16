from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.database import get_db
from app.dependencies import require_roles, user_to_public
from app.models.user import User
from app.schemas.users import UserListItem, UserListResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def list_users(
    role: UserRole | None = Query(None),
    _: User = Depends(require_roles(UserRole.director)),
    db: Session = Depends(get_db),
) -> UserListResponse:
    q = db.query(User)
    if role is not None:
        q = q.filter(User.role == role)
    users = q.order_by(User.full_name).all()
    return UserListResponse(
        items=[
            UserListItem(
                id=u.id,
                name=u.full_name,
                email=u.email,
                role=u.role,
            )
            for u in users
        ]
    )
