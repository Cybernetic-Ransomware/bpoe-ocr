import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OCRedImageResult(BaseModel):
    user_email: EmailStr
    filename: str
    ocr_result: list[str]
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    upload_date: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(populate_by_name=True)
