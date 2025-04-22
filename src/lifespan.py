from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.conf_logger import setup_logger
from src.config import DEBUG, MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY
from src.core.documentstorage.utils import MongoConnectorBuilder
from src.core.filestorage.utils import S3HealthChecker

logger = setup_logger(__name__, "main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{DEBUG=}", flush=True)
    logger.info(f"Started with {DEBUG=}")
    with S3HealthChecker(MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY) as bucket_connector:
        if not bucket_connector.healthcheck():
            print("No connection to Bucket!", flush=True)
            logger.info("Started without connection to images Bucket.")
        else:
            print("Healthcheck to Bucket has succeeded.", flush=True)
    try:
        MongoConnectorBuilder()
        print("MongoConnectorBuilder init checker succeeded.", flush=True)
    except Exception as e:
        logger.error(f"MongoDB initialization failed: {e}")
        print("No connection to MongoDB!", flush=True)
        logger.info("Started without proper initialization of document storage: MongoDB.")
    yield  # Separates code before the application starts and after it stops
    # ___ Any code to clean up resources after the application stops
