from decouple import config

config.search_path = "./docker"

MINIO_ACCESS_KEY=config("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY=config("MINIO_SECRET_KEY")
MINIO_BUCKET_NAME=config("MINIO_BUCKET_NAME")
MINIO_ENDPOINT=config("MINIO_ENDPOINT")

