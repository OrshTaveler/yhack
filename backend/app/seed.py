from __future__ import annotations

"""Демо-данные при первом запуске."""

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import hash_password
from app.models.school import ClassGroup, ClassTeacherAssignment, StudentEnrollment, Subject
from app.models.user import User

DEMO_USERS = [
    ("director@school.ru", "director123", "Иванова А.С.", UserRole.director),
    ("teacher@school.ru", "teacher123", "Петров И.В.", UserRole.teacher),
    ("student@school.ru", "student123", "Сидоров М.А.", UserRole.student),
]


def seed_demo_data(db: Session) -> None:
    users: dict[str, User] = {}
    for email, password, name, role in DEMO_USERS:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            users[role.value] = existing
            continue
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=name,
            role=role,
        )
        db.add(user)
        db.flush()
        users[role.value] = user

    if db.query(ClassGroup).first():
        db.commit()
        return

    class_5a = ClassGroup(name="5А", grade=5)
    db.add(class_5a)
    db.flush()

    math = Subject(name="Математика")
    algebra = Subject(name="Алгебра")
    db.add_all([math, algebra])
    db.flush()

    teacher = users.get("teacher")
    student = users.get("student")
    if teacher:
        db.add(ClassTeacherAssignment(class_id=class_5a.id, teacher_id=teacher.id))
    if student:
        db.add(StudentEnrollment(student_id=student.id, class_id=class_5a.id))

    db.commit()
