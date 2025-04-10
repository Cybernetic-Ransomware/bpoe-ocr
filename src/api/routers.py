from fastapi import APIRouter, File, UploadFile

from src.api.exceptions import (
    EndpointNotAllowed,
    EndpointUnexpectedException,
    FileTransferInterrupted,
    UnsupportedOCREngine,
)
from src.conf_logger import setup_logger
from src.config import (
    DEBUG,
    MINIO_READER_ACCESS_KEY,
    MINIO_READER_SECRET_KEY,
    MINIO_WRITER_ACCESS_KEY,
    MINIO_WRITER_SECRET_KEY,
)
from src.core.filestorage.utils import S3ImageReader, S3ImageUploader
from src.core.ocr.utils import PytesseractReader

logger = setup_logger(__name__, "api")


router = APIRouter()

ocr_engines = {
    'pytesseract': PytesseractReader(),
}

@router.get("/", include_in_schema=False)
async def healthcheck():
    return {"status": "OK"}

@router.post("/upload/{file_name}")
async def upload_file(file_name: str, file: UploadFile | None = None) -> dict[str, str]:
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
            bucket_connector.delete_file(file_name)
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


@router.post("/process_ocr/", response_model=dict[str, list[str]])
async def process_ocr_task(file_name: str, ocr_engine: str = 'pytesseract') -> dict[str, list[str]]:  #type: ignore[assignment]
    """
    Processes the OCR task by fetching the image from the storage, applying OCR,
    and returning the extracted text. The file is deleted from the storage after processing.

    :param file_name: str, unique file name (UUID) that exists in the bucket
    :param ocr_engine: str, the OCR engine to use (default is PytesseractReader)
    :return: dict[str, list[str]], OCR result with the file name as the key and extracted text as the value
    """
    try:
        engine = ocr_engines.get(ocr_engine)
        if not engine:
            raise UnsupportedOCREngine(message=ocr_engine)

        ocred_text = engine.ocr_file(file_name)
        logger.info(f"OCR result: {str(ocred_text)} --- for file {file_name}")
        delete_file(file_name)
        return {file_name: ocred_text.get("text", [])}
    except Exception as e:
        raise EndpointUnexpectedException(str(e)) from e
