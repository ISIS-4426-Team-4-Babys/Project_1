from .examples.user_example import user_create_example, user_update_example, user_response_example, token_response_example, login_request_example, login_response_example
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
    
    model_config = {
        "json_schema_extra": user_create_example
    }

# Update User schema
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    profile_image: Optional[str] = None
    password: Optional[str] = None

    model_config = {
        "json_schema_extra": user_update_example
    }

# Response User schema
class UserResponse(UserBase):
    id: UUID
    courses_taught: Optional[List[CourseResponseMinimal]] = []
    courses_taken: Optional[List[CourseResponseMinimal]] = []
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": user_response_example
    }

# Auth schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = {
        "json_schema_extra": token_response_example
    }

class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = {
        "json_schema_extra": login_request_example
    }
    
class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    
    model_config = {
        "json_schema_extra": login_response_example
    }