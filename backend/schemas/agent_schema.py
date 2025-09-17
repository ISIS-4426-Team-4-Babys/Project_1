from .examples.agent_examples import resource_response_example, course_response_example, agent_create_example, agent_update_example, agent_response_example
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
        "from_attributes": True,
        "json_schema_extra": resource_response_example
    }

# Embedded Course Schema
class CourseResponse(BaseModel):
    id: UUID
    name: str
    code: str
    department: str
    description: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": course_response_example
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

    model_config = {
        "json_schema_extra": agent_create_example
    }

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

    model_config = {
        "json_schema_extra": agent_update_example
    }

# Agent Response Schema
class AgentResponse(AgentBase):
    id: UUID
    associated_course: UUID
    course: Optional[CourseResponse] = None
    resources: Optional[List[ResourceResponse]] = []


    model_config = {
        "from_attributes": True,
        "json_schema_extra": agent_response_example
    }