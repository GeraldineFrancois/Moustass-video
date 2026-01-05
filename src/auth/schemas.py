from pydantic import BaseModel, EmailStr, constr
from typing import Optional


class UserCreate(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    password: constr(min_length=8)
    confirm_password: str


class UserOut(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: EmailStr
    role: str
    public_key: Optional[str]

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
