from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routers import router as api_router
from src.conf_logger import setup_logger
from src.config import DEBUG, MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY
from src.core.filestorage.utils import S3HealthChecker

logger = setup_logger(__name__, "main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{DEBUG=}", flush=True)
    logger.info(f"Started with {DEBUG=}")
    with S3HealthChecker(MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY) as bucket_connector:
        if not bucket_connector.healthcheck():
            print("No connection to Bucket!", flush=True)
            logger.info("Started without connection to DB.")
        else:
            print("Healthcheck to Bucket has succeed.", flush=True)
    yield  # Separates code before the application starts and after it stops
    # ___ Any code to clean up resources after the application stops


app = FastAPI(lifespan=lifespan)

app.include_router(api_router, prefix="/api", tags=["api"])

@app.get("/")
async def healthcheck():
    logger.info("Called first healthcheck")
    return {"status": "OK"}