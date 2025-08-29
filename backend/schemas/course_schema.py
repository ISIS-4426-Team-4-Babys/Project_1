from models.course_model import CourseDepartment
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

# Embedded user schema
class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str

    model_config = {
        "from_attributes": True
    }

# Define course base schema
class CourseBase(BaseModel):
    name: str
    code: str
    department: CourseDepartment
    description: str

# Create course (POST)
class CourseCreate(CourseBase):
    taught_by: UUID

# Update course (PUT)
class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department: Optional[CourseDepartment] = None
    description: Optional[str] = None
    taught_by: Optional[UUID] = None

# Get course (GET)
class CourseResponse(CourseBase):
    id: UUID
    taught_by: UUID
    teacher: UserResponse

    model_config = {
        "from_attributes": True
    }

