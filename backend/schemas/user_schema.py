from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from uuid import UUID
from models.user_model import UserRole

# -------- Base / Create / Update --------
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    profile_image: Optional[str] = None

class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Password must not be empty")
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    profile_image: Optional[str] = None
    password: Optional[str] = None

# -------- Responses / Auth --------
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    profile_image: Optional[str] = None

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
