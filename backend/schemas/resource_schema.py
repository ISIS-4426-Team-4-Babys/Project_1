from .examples.resource_example import agent_response_example, resource_create_example, resource_response_example
from models.agent_model import LanguageEnum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


# Embedded Agent schema 
class AgentResponse(BaseModel):
    id: UUID
    name: str
    description: str
    is_working: bool
    model: Optional[str] = None
    language: Optional[LanguageEnum] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": agent_response_example
    }

# Base Resource schema
class ResourceBase(BaseModel):
    name: str
    filetype: str
    filepath: str
    size: int
    timestamp: datetime

# Create Resource schema
class ResourceCreate(ResourceBase):
    consumed_by: UUID  
    total_docs: int
    

    model_config = {
        "json_schema_extra": resource_create_example
    }

# Response Resource schema
class ResourceResponse(ResourceBase):
    id: UUID
    consumed_by: UUID
    agent: Optional[AgentResponse] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": resource_response_example
    }

