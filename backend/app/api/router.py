from fastapi import APIRouter

from app.api.routes import auth, classes, homework, noise, schedule, stats

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(schedule.router)
api_router.include_router(homework.router)
api_router.include_router(noise.router)
api_router.include_router(classes.router)
api_router.include_router(stats.router)
