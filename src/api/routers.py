from fastapi import APIRouter, UploadFile, File

from src.config import MINIO_READER_ACCESS_KEY, MINIO_WRITER_ACCESS_KEY
from src.api.exceptions import EndpointUnexpectedException, FileTransferInterrupted
from core.filestorage.utils import S3ImageUploader, S3ImageReader


router = APIRouter()

@router.get("/", include_in_schema=False)
async def healthcheck():
    return {"message": "1"}

@router.post("/upload/{file_name}")
async def upload_file(file_name: str, file: UploadFile = File(...)):
    try:
        with S3ImageUploader(MINIO_WRITER_ACCESS_KEY) as bucket_connector:
            success = bucket_connector.upload_file(file_obj=file.file, file_name=file_name)
            if success:
                return {"message": f"File '{file_name}' uploaded successfully"}
            raise FileTransferInterrupted()
    except Exception as e:
        raise EndpointUnexpectedException(str(e))

@router.get("/download/{file_name}")
async def download_file(file_name: str):
    try:
        with S3ImageReader(MINIO_READER_ACCESS_KEY) as bucket_connector:
            return bucket_connector.download_file(file_name=file_name)
    except Exception as e:
        raise EndpointUnexpectedException(str(e))
