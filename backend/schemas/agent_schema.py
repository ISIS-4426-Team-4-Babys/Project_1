from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from models.agent_model import LanguageEnum
from models.course_model import CourseDepartment

# Embedded Course Schema
class CourseResponse(BaseModel):
    name: str
    code: str
    department: CourseDepartment
    description: str
    
    model_config = {
        "from_attributes": True
    }

# Define Agent base schema
class AgentBase(BaseModel):
    name: str
    description: str
    is_working: bool
    system_prompt: str
    model: str
    language: LanguageEnum
    retrieval_k: int

# Create agent (POST)
class AgentCreate(AgentBase):
    associated_course: UUID

# Update agent (PUT)
class AgentUpdate(AgentBase):
    name: Optional[str] = None
    description: Optional[str] = None
    is_working: Optional[bool] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    language: Optional[LanguageEnum] = None
    retrieval_k: Optional[int] = None
    associated_course: Optional[UUID] = None

# Get Agent (GET)
class AgentResponse(AgentBase):
    id: UUID
    associated_course: UUID
    course: CourseResponse
    
    model_config = {
        "from_attributes": True
    }