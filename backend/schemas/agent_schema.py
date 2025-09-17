from models.agent_model import LanguageEnum
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

# Examples
UUID_AGENT = "11111111-2222-3333-4444-555555555555"
UUID_COURSE = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
UUID_RESOURCE = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

# Embedded Resource Schema
class ResourceResponse(BaseModel):
    id: UUID
    name: str
    filetype: str
    filepath: str
    size: int


    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": UUID_RESOURCE,
                "name": "Week 1 - Secure Coding Slides",
                "filetype": "application/pdf",
                "filepath": "/data/resources/SEC-101/week1.pdf",
                "size": 2487310
            }]
        }
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
        "json_schema_extra": {
            "examples": [{
                "id": UUID_COURSE,
                "name": "Secure Coding 101",
                "code": "SEC-101",
                "department": "Cybersecurity",
                "description": "Intro to secure development practices"
            }]
        }
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
        "json_schema_extra": {
            "examples": [{
                "name": "Agent Introduction",
                "description": "Answers FAQs and onboarding questions",
                "is_working": True,
                "system_prompt": "You are the CyberLearn course agent. Answer in Spanish, be concise and cite sources when possible.",
                "model": "gpt-4o-mini",
                "language": "es",
                "retrieval_k": 25,
                "associated_course": UUID_COURSE
            }]
        }
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
        "json_schema_extra": {
            "examples": [{
                "description": "Adds grading rubric guidance",
                "is_working": False,
                "retrieval_k": 30
            }]
        }
    }

# Agent Response Schema
class AgentResponse(AgentBase):
    id: UUID
    associated_course: UUID
    course: Optional[CourseResponse] = None
    resources: Optional[List[ResourceResponse]] = []


    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": UUID_AGENT,
                "name": "Agent Introduction",
                "description": "Answers FAQs and onboarding questions",
                "is_working": True,
                "system_prompt": "You are the CyberLearn course agent. Answer in Spanish, be concise and cite sources when possible.",
                "model": "gpt-4o-mini",
                "language": "es",
                "retrieval_k": 25,
                "associated_course": UUID_COURSE,
                "course": {
                    "id": UUID_COURSE,
                    "name": "Secure Coding 101",
                    "code": "SEC-101",
                    "department": "Cybersecurity",
                    "description": "Intro to secure development practices"
                },
                "resources": []
            }]
        }
    }