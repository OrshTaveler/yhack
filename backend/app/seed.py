from __future__ import annotations

"""Демо-данные при первом запуске."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.enums import HomeworkStatus, UserRole
from app.core.security import hash_password
from app.models.homework import HomeworkSubmission
from app.models.school import ClassGroup, ClassTeacherAssignment, StudentEnrollment, Subject
from app.models.user import User

DEMO_USERS = [
    ("director@school.ru", "director123", "Иванова А.С.", UserRole.director),
    ("teacher@school.ru", "teacher123", "Петров И.В.", UserRole.teacher),
    ("student@school.ru", "student123", "Сидоров М.А.", UserRole.student),
]

# Демо-предметы школы
DEMO_SUBJECTS = [
    "Математика",
    "Русский язык",
    "Физика",
    "История",
    "Биология",
    "Английский язык",
]

# Демо-домашки ученика: (предмет, оценка ИИ, оценка учителя, дней назад, комментарий ИИ)
# Подобраны так, чтобы профиль был «живой»: сильные и слабые предметы.
DEMO_HOMEWORKS = [
    ("Математика", 5.0, 5.0, 40, "Все примеры решены верно, аккуратное оформление."),
    ("Русский язык", 3.0, 3.0, 38, "Три орфографические ошибки, пунктуация в сложных предложениях."),
    ("История", 3.0, 2.0, 35, "Даты перепутаны, не раскрыта причина события."),
    ("Физика", 4.0, 4.0, 30, "Формула применена верно, ошибка в единицах измерения."),
    ("Математика", 4.0, 5.0, 25, "Небольшая описка в вычислениях, ход решения правильный."),
    ("Английский язык", 4.0, 4.0, 21, "Хороший словарный запас, ошибки во временах глаголов."),
    ("Русский язык", 3.0, 4.0, 14, "Прогресс заметен, осталась пара ошибок в окончаниях."),
    ("История", 3.0, 3.0, 10, "Материал выучен лучше, но хронология всё ещё путается."),
    ("Математика", 5.0, None, 4, "Работа проверена ИИ, замечаний почти нет."),
    ("Физика", 4.0, None, 2, "ИИ-проверка: решение верное, проверьте размерности."),
    ("Биология", 4.0, 4.0, 18, "Верно описан фотосинтез, уточните роль хлорофилла."),
]


def _ensure_subjects(db: Session) -> None:
    """Добавляет предметы, которых нет в уже созданной БД (История, Биология и др.)."""
    for name in DEMO_SUBJECTS:
        if db.query(Subject).filter(Subject.name == name).first() is None:
            db.add(Subject(name=name))
    db.flush()


def _ensure_demo_teacher_assignment(db: Session) -> None:
    """Если БД уже была создана без привязки учителя к классу — добавить."""
    teacher = db.query(User).filter(User.email == "teacher@school.ru").first()
    class_5a = db.query(ClassGroup).filter(ClassGroup.name == "5А").first()
    if not teacher or not class_5a:
        return
    exists = (
        db.query(ClassTeacherAssignment)
        .filter(
            ClassTeacherAssignment.teacher_id == teacher.id,
            ClassTeacherAssignment.class_id == class_5a.id,
        )
        .first()
    )
    if not exists:
        db.add(ClassTeacherAssignment(class_id=class_5a.id, teacher_id=teacher.id))


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
        _ensure_subjects(db)
        _ensure_demo_teacher_assignment(db)
        db.commit()
        return

    class_5a = ClassGroup(name="5А", grade=5, students_count=25)
    db.add(class_5a)
    db.flush()

    subjects: dict[str, Subject] = {}
    for name in DEMO_SUBJECTS:
        subject = Subject(name=name)
        db.add(subject)
        db.flush()
        subjects[name] = subject

    teacher = users.get("teacher")
    student = users.get("student")
    if teacher:
        db.add(ClassTeacherAssignment(class_id=class_5a.id, teacher_id=teacher.id))
    if student:
        db.add(StudentEnrollment(student_id=student.id, class_id=class_5a.id))

        # Демо-домашки ученика для наполнения профиля
        now = datetime.now(timezone.utc)
        for subject_name, ai_grade, teacher_grade, days_ago, comment in DEMO_HOMEWORKS:
            subject = subjects.get(subject_name)
            if subject is None:
                continue
            status = (
                HomeworkStatus.teacher_reviewed
                if teacher_grade is not None
                else HomeworkStatus.ai_reviewed
            )
            db.add(
                HomeworkSubmission(
                    student_id=student.id,
                    class_id=class_5a.id,
                    subject_id=subject.id,
                    file_key=f"demo/{subject_name}-{days_ago}.jpg",
                    status=status,
                    ai_grade=ai_grade,
                    ai_comment=comment,
                    teacher_grade=teacher_grade,
                    submitted_at=now - timedelta(days=days_ago),
                )
            )

    db.commit()
