import io
import uuid
from functools import lru_cache

from minio import Minio
from minio.error import S3Error

from app.config import get_settings


@lru_cache
def get_minio_client() -> Minio:
    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_buckets() -> None:
    settings = get_settings()
    client = get_minio_client()
    for bucket in (settings.minio_bucket_homework, settings.minio_bucket_lesson_media):
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)


def upload_file(
    bucket: str,
    file_data: io.BytesIO,
    content_type: str,
    prefix: str = "",
) -> str:
    """Upload file and return object key."""
    key = f"{prefix}{uuid.uuid4().hex}"
    length = file_data.getbuffer().nbytes
    file_data.seek(0)
    client = get_minio_client()
    client.put_object(bucket, key, file_data, length, content_type=content_type)
    return key


def get_presigned_url(bucket: str, object_key: str, expires_hours: int = 24) -> str:
    from datetime import timedelta

    client = get_minio_client()
    return client.presigned_get_object(bucket, object_key, expires=timedelta(hours=expires_hours))


def download_file(bucket: str, object_key: str) -> bytes:
    """Скачивает файл из MinIO и возвращает его байты."""
    client = get_minio_client()
    response = None
    try:
        response = client.get_object(bucket, object_key)
        return response.read()
    finally:
        if response is not None:
            response.close()
            response.release_conn()


def delete_object(bucket: str, object_key: str) -> None:
    client = get_minio_client()
    try:
        client.remove_object(bucket, object_key)
    except S3Error:
        pass
