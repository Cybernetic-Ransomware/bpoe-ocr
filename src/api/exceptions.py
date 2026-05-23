from fastapi import HTTPException
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status_code: int
    error: str
    detail: str


class FileTransferInterrupted(HTTPException):
    def __init__(self):
        super().__init__(status_code=500, detail="File transfer interrupted")


class FileBlobHasNoExtension(HTTPException):
    def __init__(self):
        super().__init__(status_code=415, detail="File name was provided without an extension")


class EndpointNotAllowed(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail="Endpoint not allowed in current deployment")


class UnsupportedOCREngine(HTTPException):
    def __init__(self, code: int = 400, message: str = ""):
        super().__init__(status_code=code, detail=f"Unsupported OCR engine: {message}")
