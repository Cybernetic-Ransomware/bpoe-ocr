from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.api.exceptions import ErrorResponse
from src.api.routers import router as api_router
from src.conf_logger import setup_logger
from src.config import DEBUG
from src.lifespan import lifespan

logger = setup_logger(__name__, "main")

app = FastAPI(lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if (DEBUG or exc.status_code < 500) else "Internal server error"
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status_code=exc.status_code,
            error=type(exc).__name__,
            detail=detail,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status_code=500,
            error="InternalServerError",
            detail=str(exc) if DEBUG else "Unexpected error",
        ).model_dump(),
    )


app.include_router(api_router, prefix="/api", tags=["api"])


@app.get("/")
async def healthcheck():
    logger.info("Called first healthcheck")
    return {"status": "OK"}
