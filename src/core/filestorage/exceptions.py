from fastapi import HTTPException

from src.config import DEBUG


class MinIOConnectorError(HTTPException):
    def __init__(self, code: int = 503, message: str = ""):
        detail = message if (DEBUG or code < 500) else "Storage error"
        super().__init__(status_code=code, detail=detail)
