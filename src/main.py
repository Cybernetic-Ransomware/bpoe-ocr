from fastapi import FastAPI

from src.api.routers import router as api_router

app = FastAPI()

app.include_router(api_router, prefix="/api1", tags=["api"])


@app.get("/")
async def root():
    return {"message": "Hello World"}
