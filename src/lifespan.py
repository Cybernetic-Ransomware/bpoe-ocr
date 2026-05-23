from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.conf_logger import setup_logger
from src.config import DEBUG, MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY, missing_required_config
from src.core.documentstorage.utils import MongoConnectorBuilder
from src.core.filestorage.utils import S3HealthChecker

logger = setup_logger(__name__, "main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    missing = missing_required_config()
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")
    logger.info(f"Started with {DEBUG=}")
    with S3HealthChecker(MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY) as bucket_connector:
        if not bucket_connector.healthcheck():
            logger.warning("Started without connection to images Bucket.")
        else:
            logger.info("Healthcheck to Bucket has succeeded.")
    try:
        await MongoConnectorBuilder().initialize()
        logger.info("MongoConnectorBuilder init checker succeeded.")
    except Exception as e:
        logger.error(f"MongoDB initialization failed: {e}")
        logger.warning("Started without proper initialization of document storage: MongoDB.")
    yield
