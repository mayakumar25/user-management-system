from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    
    email: str
    username: str
    password: str
    role: str = "user"


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    department: str
    college: str
    profile_photo: str
    can_edit: bool
    role: str

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    username: Optional[str]
    department: Optional[str]
    college: Optional[str]
    profile_photo: Optional[str]
