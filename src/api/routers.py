from fastapi import APIRouter, UploadFile, File

from src.config import (DEBUG, MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY,
                        MINIO_WRITER_ACCESS_KEY, MINIO_WRITER_SECRET_KEY)
from src.api.exceptions import EndpointUnexpectedException, FileTransferInterrupted, EndpointNotAllowed
from src.core.filestorage.utils import S3ImageUploader, S3ImageReader
from src.core.ocr.utils import PytesseractReader

router = APIRouter()

@router.get("/", include_in_schema=False)
async def healthcheck():
    return {"status": "OK"}

@router.post("/upload/{file_name}")
async def upload_file(file_name: str, file: UploadFile = None) -> dict[str, str]:
    """
    API Gateway uploads an image directly to S3/MiniIO.

    :param file_name: str, unique file name (UUID), also used as frontend-gateway socket connection_id.
    :param file: UploadFile, binary image blob received from frontend.
    :return: dict[str, str], confirmation message.
    """
    if file is None:
        file = File(...)

    try:
        with S3ImageUploader(MINIO_WRITER_ACCESS_KEY, MINIO_WRITER_SECRET_KEY) as bucket_connector:
            success = bucket_connector.upload_file(file_obj=file.file, file_name=file_name)
            if success:
                return {"message": f"File '{file_name}' uploaded successfully"}
            raise FileTransferInterrupted()
    except Exception as e:
        raise EndpointUnexpectedException(str(e)) from e

def delete_file(file_name: str) -> None:
    try:
        with S3ImageUploader(MINIO_WRITER_ACCESS_KEY, MINIO_WRITER_SECRET_KEY) as bucket_connector:
            bucket_connector.delete_object(file_name)
    except Exception as e:
        raise EndpointUnexpectedException(str(e)) from e

@router.get("/download/{file_name}")
async def download_file(file_name: str):
    """
    Downloads a file from the storage. This endpoint is intended for testing purposes only.

    :param file_name: str, unique file name (UUID) that exists in the bucket
    :return: file content or appropriate error message if the file cannot be found
    """
    if not DEBUG:
        raise EndpointNotAllowed()
    try:
        with S3ImageReader(MINIO_READER_ACCESS_KEY, MINIO_READER_SECRET_KEY) as bucket_connector:
            return bucket_connector.download_file(file_name=file_name)
    except Exception as e:
        raise EndpointUnexpectedException(str(e)) from e


@router.post("/process_ocr/")
async def process_ocr_task(file_name: str, ocr_engine: callable = PytesseractReader) -> dict[str, dict[str]]:
    """
    Processes the OCR task by fetching the image from the storage, applying OCR,
    and returning the extracted text. The file is deleted from the storage after processing.

    :param file_name: str, unique file name (UUID) that exists in the bucket
    :param ocr_engine: callable, the OCR engine to use (default is PytesseractReader
    :return: dict[str, dict[str]], OCR result with the file name as the key and extracted text as the value
    """
    try:
        ocred_text = ocr_engine.ocr_file(file_name)
        delete_file(file_name)
        return {file_name: ocred_text}
    except Exception as e:
        raise EndpointUnexpectedException(str(e)) from e
