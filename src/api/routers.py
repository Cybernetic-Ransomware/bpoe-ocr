from fastapi import APIRouter


router = APIRouter()


@router.get("/", include_in_schema=False)
async def healthcheck():
    return {"message": "1"}
