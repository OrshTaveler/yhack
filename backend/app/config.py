from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://teacher:teacher@127.0.0.1:5433/teacher_assistant"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minio"
    minio_secret_key: str = "minio123"
    minio_secure: bool = False
    minio_bucket_homework: str = "homework"
    minio_bucket_lesson_media: str = "lesson-media"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    api_prefix: str = "/api"

    # Yandex AI Studio (Vision OCR, YandexGPT, AI Search)
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_knowledge_index_id: str = ""

    # text.ru — антиплагиат
    textru_userkey: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
