from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.enums import UserRole
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.schedule import ScheduleSlot
from app.models.school import StudentEnrollment
from app.models.user import User
from app.schemas.schedule import ScheduleGenerateRequest, ScheduleResponse, ScheduleSlotOut
from app.services.schedule_generator import generate_schedule

router = APIRouter(prefix="/schedule", tags=["schedule"])


def _slots_for_user(db: Session, user: User) -> list[ScheduleSlot]:
    q = (
        db.query(ScheduleSlot)
        .options(
            joinedload(ScheduleSlot.subject),
            joinedload(ScheduleSlot.class_group),
            joinedload(ScheduleSlot.teacher),
        )
    )
    if user.role == UserRole.teacher:
        return q.filter(ScheduleSlot.teacher_id == user.id).order_by(
            ScheduleSlot.day_of_week, ScheduleSlot.period
        ).all()
    if user.role == UserRole.student:
        class_ids = [
            e.class_id
            for e in db.query(StudentEnrollment).filter(StudentEnrollment.student_id == user.id).all()
        ]
        if not class_ids:
            return []
        return q.filter(ScheduleSlot.class_id.in_(class_ids)).order_by(
            ScheduleSlot.day_of_week, ScheduleSlot.period
        ).all()
    return q.order_by(ScheduleSlot.day_of_week, ScheduleSlot.period).all()


def _to_slot_out(slot: ScheduleSlot) -> ScheduleSlotOut:
    return ScheduleSlotOut(
        id=slot.id,
        day_of_week=slot.day_of_week,
        period=slot.period,
        subject_id=slot.subject_id,
        subject_name=slot.subject.name,
        class_id=slot.class_id,
        class_name=slot.class_group.name,
        teacher_id=slot.teacher_id,
        room=slot.room,
    )


@router.get("/me", response_model=ScheduleResponse)
def get_my_schedule(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    slots = _slots_for_user(db, user)
    return ScheduleResponse(slots=[_to_slot_out(s) for s in slots])


@router.get("/user/{user_id}", response_model=ScheduleResponse)
def get_user_schedule(
    user_id: UUID,
    current: User = Depends(require_roles(UserRole.director)),
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    slots = _slots_for_user(db, target)
    return ScheduleResponse(slots=[_to_slot_out(s) for s in slots])


@router.post("/generate", response_model=ScheduleResponse)
def generate(
    payload: ScheduleGenerateRequest,
    _: User = Depends(require_roles(UserRole.director)),
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    generate_schedule(db, payload)
    loaded = (
        db.query(ScheduleSlot)
        .options(
            joinedload(ScheduleSlot.subject),
            joinedload(ScheduleSlot.class_group),
        )
        .all()
    )
    return ScheduleResponse(slots=[_to_slot_out(s) for s in loaded])
