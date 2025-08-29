from models.user_model import UserRole
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID


# Embedded schemas 
class CourseResponseMinimal(BaseModel):
    id: UUID
    name: str
    code: str

    model_config = {
        "from_attributes": True
    }

class AgentResponseMinimal(BaseModel):
    id: UUID
    name: str
    description: str
    is_working: bool

    model_config = {
        "from_attributes": True
    }

# Base User schema
class UserBase(BaseModel):
    name: str
    email: str
    role: UserRole
    profile_image: Optional[str] = None

# Create User schema
class UserCreate(UserBase):
    password: str

# Update User schema
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    profile_image: Optional[str] = None
    password: Optional[str] = None

# Response User schema
class UserResponse(UserBase):
    id: UUID
    courses_taught: Optional[List[CourseResponseMinimal]] = []
    courses_taken: Optional[List[CourseResponseMinimal]] = []

    model_config = {
        "from_attributes": True
    }

# Auth schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: str
    password: str
