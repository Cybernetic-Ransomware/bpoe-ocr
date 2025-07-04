from fastapi import HTTPException


class FileNotFoundInBucket(HTTPException):
    def __init__(self, code:int = 404, message:str = ''):
        super().__init__(status_code=code, detail=f"File not found, \n {message}")
