from fastapi import APIRouter

from app.api.routes import (
    auth,
    classes,
    homework,
    lesson,
    noise,
    profile,
    schedule,
    stats,
    subjects,
    users,
    lesson_report_yandex,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(schedule.router)
api_router.include_router(homework.router)
api_router.include_router(lesson.router)
api_router.include_router(noise.router)
api_router.include_router(profile.router)
api_router.include_router(classes.router)
api_router.include_router(stats.router)
api_router.include_router(users.router)
api_router.include_router(subjects.router)
api_router.include_router(lesson_report_yandex.router)
