from pydantic import BaseModel, EmailStr


class OcrRequest(BaseModel):
    user_email: EmailStr
