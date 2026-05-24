from logging import INFO
from pathlib import Path

from decouple import config

config.search_path = str(Path(__file__).resolve().parent.parent / "docker")

MINIO_ACCESS_KEY: str = config("MINIO_ACCESS_KEY", default="")
MINIO_SECRET_KEY: str = config("MINIO_SECRET_KEY", default="")
MINIO_BUCKET_NAME: str = config("MINIO_BUCKET_NAME", default="")
MINIO_ENDPOINT: str = config("MINIO_ENDPOINT", default="")

MINIO_READER_ACCESS_KEY: str = config("MINIO_READER_ACCESS_KEY", default="")
MINIO_WRITER_ACCESS_KEY: str = config("MINIO_WRITER_ACCESS_KEY", default="")
MINIO_WRITER_SECRET_KEY: str = config("MINIO_WRITER_SECRET_KEY", default="")
MINIO_READER_SECRET_KEY: str = config("MINIO_READER_SECRET_KEY", default="")

MONGO_ADMIN_URI: str = config("MONGO_ADMIN_URI", default="")
MONGO_WRITER_URI: str = config("MONGO_WRITER_URI", default="")
MONGO_DB: str = config("MONGO_DB", default="")
MONGO_COLLECTION: str = config("MONGO_COLLECTION", default="")

DEBUG: bool = config("DEBUG", default=False, cast=bool)
LOGGER_LEVEL = 10 if DEBUG else INFO

_REQUIRED: dict[str, str] = {
    "MINIO_BUCKET_NAME": MINIO_BUCKET_NAME,
    "MINIO_ENDPOINT": MINIO_ENDPOINT,
    "MINIO_READER_ACCESS_KEY": MINIO_READER_ACCESS_KEY,
    "MINIO_WRITER_ACCESS_KEY": MINIO_WRITER_ACCESS_KEY,
    "MINIO_WRITER_SECRET_KEY": MINIO_WRITER_SECRET_KEY,
    "MINIO_READER_SECRET_KEY": MINIO_READER_SECRET_KEY,
    "MONGO_ADMIN_URI": MONGO_ADMIN_URI,
    "MONGO_WRITER_URI": MONGO_WRITER_URI,
    "MONGO_DB": MONGO_DB,
    "MONGO_COLLECTION": MONGO_COLLECTION,
}


def missing_required_config() -> list[str]:
    return [key for key, value in _REQUIRED.items() if not value]
