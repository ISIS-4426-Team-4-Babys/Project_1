from models.agent_model import LanguageEnum
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

# Embedded Resource Schema
class ResourceResponse(BaseModel):
    id: UUID
    name: str
    filetype: str
    filepath: str
    size: int

    model_config = {
        "from_attributes": True
    }

# Embedded Course Schema
class CourseResponse(BaseModel):
    id: UUID
    name: str
    code: str
    department: str
    description: str

    model_config = {
        "from_attributes": True
    }

# Base Agent Schema
class AgentBase(BaseModel):
    name: str
    description: str
    is_working: bool
    system_prompt: str
    model: str
    language: LanguageEnum
    retrieval_k: int

# Agent Create Schema
class AgentCreate(AgentBase):
    associated_course: UUID

# Agent Update Schema
class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_working: Optional[bool] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    language: Optional[LanguageEnum] = None
    retrieval_k: Optional[int] = None
    associated_course: Optional[UUID] = None

# Agent Response Schema
class AgentResponse(AgentBase):
    id: UUID
    associated_course: UUID
    course: Optional[CourseResponse] = None
    resources: Optional[List[ResourceResponse]] = []

    model_config = {
        "from_attributes": True
    }