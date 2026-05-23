from fastapi import HTTPException


class ConnectorMethodNotAllowed(HTTPException):
    def __init__(self, code: int = 503, class_name: str = ""):
        super().__init__(status_code=code, detail=f"Method not allowed in connector class: {class_name}")
