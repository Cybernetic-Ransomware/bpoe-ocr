from fastapi import HTTPException


class MinIOConnectorError(HTTPException):
    def __init__(self, code: int = 503, message: str = ""):
        super().__init__(status_code=code, detail=message)
