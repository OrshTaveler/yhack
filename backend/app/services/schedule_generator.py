from __future__ import annotations

"""Простой генератор расписания: равномерно разносит пары по сетке."""

import random
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.schedule import ClassSubjectHours, ScheduleSlot
from app.models.school import ClassGroup, Subject
from app.schemas.schedule import ClassInput, ScheduleGenerateRequest, SubjectHoursInput
from app.utils.class_name import parse_grade_from_class_name


def _get_or_create_class(db: Session, item: ClassInput) -> ClassGroup:
    grade = parse_grade_from_class_name(item.name)
    existing = db.query(ClassGroup).filter(ClassGroup.name == item.name).first()
    if existing:
        existing.grade = grade
        existing.students_count = item.students_count
        return existing
    group = ClassGroup(name=item.name.strip(), grade=grade, students_count=item.students_count)
    db.add(group)
    db.flush()
    return group


def _get_or_create_subject(db: Session, name: str) -> Subject:
    existing = db.query(Subject).filter(Subject.name == name).first()
    if existing:
        return existing
    subject = Subject(name=name)
    db.add(subject)
    db.flush()
    return subject


def generate_schedule(db: Session, payload: ScheduleGenerateRequest) -> list[ScheduleSlot]:
    """Удаляет старые слоты затронутых классов и создаёт новые."""
    class_map: dict[str, ClassGroup] = {}
    for c in payload.classes:
        class_map[c.name] = _get_or_create_class(db, c)

    subject_entities: dict[str, Subject] = {}
    for s in payload.subjects:
        subject_entities[s.subject_name] = _get_or_create_subject(db, s.subject_name)

    for class_name, group in class_map.items():
        db.query(ScheduleSlot).filter(ScheduleSlot.class_id == group.id).delete()
        db.query(ClassSubjectHours).filter(ClassSubjectHours.class_id == group.id).delete()

    slots: list[ScheduleSlot] = []
    days = list(range(payload.days_per_week))
    periods = list(range(1, payload.periods_per_day + 1))
    grid: dict[tuple[int, int], bool] = {}

    for class_name, group in class_map.items():
        lessons: list[tuple[UUID, int]] = []
        for sh in payload.subjects:
            subj = subject_entities[sh.subject_name]
            db.add(
                ClassSubjectHours(
                    class_id=group.id,
                    subject_id=subj.id,
                    hours_per_week=sh.hours_per_week,
                )
            )
            for _ in range(sh.hours_per_week):
                lessons.append((subj.id, sh.hours_per_week))

        random.shuffle(lessons)
        for subject_id, _ in lessons:
            placed = False
            attempts = days * periods
            random.shuffle(days)
            for day in days:
                for period in periods:
                    key = (day, period)
                    if key in grid:
                        continue
                    grid[key] = True
                    slot = ScheduleSlot(
                        class_id=group.id,
                        subject_id=subject_id,
                        day_of_week=day,
                        period=period,
                    )
                    db.add(slot)
                    slots.append(slot)
                    placed = True
                    break
                if placed:
                    break
            if not placed:
                # fallback: allow collision on same cell for different classes
                day = random.choice(days)
                period = random.choice(periods)
                slot = ScheduleSlot(
                    class_id=group.id,
                    subject_id=subject_id,
                    day_of_week=day,
                    period=period,
                )
                db.add(slot)
                slots.append(slot)

    db.commit()
    return slots
