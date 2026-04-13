from pydantic import BaseModel, EmailStr

class PlayerCreate(BaseModel):
    username: str
    email: EmailStr