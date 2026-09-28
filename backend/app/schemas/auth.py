from pydantic import BaseModel, EmailStr
from typing import Optional


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
