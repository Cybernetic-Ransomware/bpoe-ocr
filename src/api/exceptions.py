from fastapi import HTTPException


class EndpointUnexpectedException(HTTPException):
    def __init__(self, message: str= ""):
        super().__init__(status_code=404, detail=f"Unexpected Endpoint Error: {message}")

class FileTransferInterrupted(HTTPException):
    def __init__(self):
        super().__init__(status_code=500, detail="File transfer interrupted")
