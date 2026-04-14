from pydantic import BaseModel, EmailStr
from datetime import datetime

class PlayerCreate(BaseModel):
    username: str
    email: EmailStr


class PlayerResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}