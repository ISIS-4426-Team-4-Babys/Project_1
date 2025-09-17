from models.user_model import UserRole
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

# Examples
UUID_USER = "9f8f5e64-5717-4562-b3fc-2c963f66afa6"
UUID_COURSE = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

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
        "json_schema_extra": {
            "examples": [{
                "name": "John Doe",
                "email": "john.doe@example.edu",
                "role": "student",
                "profile_image": "https://cdn.example.com/u/juan.png",
                "password": "S3cure!Passw0rd"
            }]
        }
    }

# Update User schema
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    profile_image: Optional[str] = None
    password: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "John Doe",
                "role": "professor",
                "password": "New!S3cureP4ss"
            }]
        }
    }

# Response User schema
class UserResponse(UserBase):
    id: UUID
    courses_taught: Optional[List[CourseResponseMinimal]] = []
    courses_taken: Optional[List[CourseResponseMinimal]] = []

    model_config = {
        "from_attributes": True
    }
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": UUID_USER,
                "name": "John Doe",
                "email": "john.doe@example.edu",
                "role": "student",
                "profile_image": "https://cdn.example.com/u/juan.png",
                "courses_taught": [],
                "courses_taken": []
            }]
        }
    }

# Auth schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }]
        }
    }

class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "john.doe@example.edu",
                "password": "S3cure!Passw0rd"
            }]
        }
    }
    
class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "user": {
                    "id": UUID_USER,
                    "name": "John Doe",
                    "email": "john.doe@example.edu",
                    "role": "student",
                    "profile_image": "https://cdn.example.com/u/juan.png",
                    "courses_taught": [{
                        "id": UUID_COURSE,
                        "name": "Secure Coding 101",
                        "code": "SEC-101"
                    }],
                    "courses_taken": [{
                        "id": "7c6c1d2e-aaaa-bbbb-cccc-ddddeeeeffff",
                        "name": "Networks & Security",
                        "code": "NET-201"
                    }]
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }]
        }
    }