from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.database import Base, engine
from app import models  # noqa: F401 — register models
from app.db_startup import ensure_schema_updates, wait_for_db
from app.services.storage import ensure_buckets
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
    try:
        ensure_buckets()
    except Exception:
        pass  # MinIO may start later
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Помощник учителя API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()


@app.get("/health")
def health():
    return {"status": "ok"}
