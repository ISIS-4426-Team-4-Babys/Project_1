from models.agent_model import LanguageEnum
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

# Examples
UUID_COURSE = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
UUID_TEACHER = "9f8f5e64-5717-4562-b3fc-2c963f66afa6"
UUID_AGENT = "11111111-2222-3333-4444-555555555555"
UUID_STUDENT = "77777777-8888-9999-aaaa-bbbbbbbbbbbb"

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
        "json_schema_extra": {
            "examples": [{
                "name": "Secure Coding 101",
                "code": "SEC-101",
                "department": "Cybersecurity",
                "description": "Intro to secure development practices",
                "taught_by": UUID_TEACHER
            }]
        }
    }

# Update Course schema
class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    taught_by: Optional[UUID] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "code": "SEC-101H",
                "description": "Updated syllabus with OWASP Top 10"
            }]
        }
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
        "json_schema_extra": {
            "examples": [{
                "id": UUID_COURSE,
                "name": "Secure Coding 101",
                "code": "SEC-101",
                "department": "Cybersecurity",
                "description": "Intro to secure development practices",
                "taught_by": UUID_TEACHER,
                "teacher": {
                    "id": UUID_TEACHER,
                    "name": "Dr. Alice Mendoza",
                    "email": "alice.mendoza@example.edu"
                },
                "agents": [],
                "students": []
            }]
        }
    }
