from fastapi import HTTPException


class MinIOConnectorError(HTTPException):
    def __init__(self, code:int = 503, message:str = ''):
        super().__init__(status_code=code, detail=f"Access denied: cannot connect to MiniIO, \n {message}")

class ConnectorMethodNotAllowed(HTTPException):
    def __init__(self, code:int = 503, class_name:str = ''):
        super().__init__(status_code=code, detail=f"Method not allowed in connector class: {class_name}")
