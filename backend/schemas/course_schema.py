from .examples.course_example import course_create_example, course_update_example, course_response_example
from models.agent_model import LanguageEnum
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID


# Embedded User schema
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str

    model_config = {
        "from_attributes": True
    }

# Embedded Agent schema
class AgentResponse(BaseModel):
    id: UUID
    name: str
    description: str
    is_working: bool
    system_prompt: str
    model: str
    language: LanguageEnum
    retrieval_k: int

    model_config = {
        "from_attributes": True
    }

# Base Course schema
class CourseBase(BaseModel):
    name: str
    code: str
    department: str
    description: str

# Create Course schema
class CourseCreate(CourseBase):
    taught_by: UUID
    
    model_config = {
        "json_schema_extra": course_create_example
    }

# Update Course schema
class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    taught_by: Optional[UUID] = None
    
    model_config = {
        "json_schema_extra": course_update_example
    }

# Response Course schema
class CourseResponse(CourseBase):
    id: UUID
    taught_by: UUID
    teacher: UserResponse
    agents: Optional[List[AgentResponse]] = []
    students: Optional[List[UserResponse]] = []

    model_config = {
        "from_attributes": True
    }


    model_config = {
        "from_attributes": True,
        "json_schema_extra": course_response_example
    }
