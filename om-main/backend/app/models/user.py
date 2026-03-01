from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    phone: Optional[str] = None
    shop_id: Optional[str] = None

class UserRegister(UserBase):
    password: str
    name: str
    age: Optional[int] = None

class UserLogin(BaseModel):
    phone: Optional[str] = None
    shop_id: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    phone: Optional[str] = None
    shop_id: Optional[str] = None
    role: str  # "user" or "admin"

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None
    session_id: Optional[str] = None
