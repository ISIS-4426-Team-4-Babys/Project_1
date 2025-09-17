from models.agent_model import LanguageEnum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

# Examples
UUID_AGENT = "11111111-2222-3333-4444-555555555555"
UUID_RESOURCE = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
ISO_TS = "2025-01-15T14:32:00Z"

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
        "json_schema_extra": {
            "examples": [{
                "id": UUID_AGENT,
                "name": "Agent Introduction",
                "description": "Answers FAQs and onboarding questions",
                "is_working": True,
                "model": "gpt-4o-mini",
                "language": "es"
            }]
        }
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
        "json_schema_extra": {
            "examples": [{
                "name": "Week 1 - Secure Coding Slides",
                "filetype": "application/pdf",
                "filepath": "/data/resources/SEC-101/week1.pdf",
                "size": 2487310,
                "timestamp": ISO_TS,
                "consumed_by": UUID_AGENT,
                "total_docs": 12
            }]
        }
    }

# Response Resource schema
class ResourceResponse(ResourceBase):
    id: UUID
    consumed_by: UUID
    agent: Optional[AgentResponse] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": UUID_RESOURCE,
                "name": "Week 1 - Secure Coding Slides",
                "filetype": "application/pdf",
                "filepath": "/data/resources/SEC-101/week1.pdf",
                "size": 2487310,
                "timestamp": ISO_TS,  
                "consumed_by": UUID_AGENT,
                "agent": {
                    "id": UUID_AGENT,
                    "name": "Agent Introduction",
                    "description": "Answers FAQs and onboarding questions",
                    "is_working": True,
                    "model": "gpt-4o-mini",
                    "language": "es"
                }
            }]
        }
    }

