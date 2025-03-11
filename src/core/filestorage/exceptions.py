from fastapi import HTTPException


class MinIOConnectorError(HTTPException):
    def __init__(self, code:int = 503, message:str = ''):
        super().__init__(status_code=503, detail=f"Access denied: cannot connect to MiniIO, \n {message}")

class ConnectorMethodNotAllowed(HTTPException):
    def __init__(self, code:int = 405, class_name:str = ''):
        super().__init__(status_code=503, detail=f"Method not allowed in connector class: {class_name}")
