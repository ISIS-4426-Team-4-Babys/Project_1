from models.resource_model import FileTypeEnum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

# Embedded agent schema
class AgentResponse(BaseModel):
    id: UUID
    name: str
    description: str
    is_working: bool

    model_config = {
        "from_attributes": True
    }

# Define resource base schema
class ResourceBase(BaseModel):
    name: str
    filetype: FileTypeEnum
    size: int
    timestamp: datetime

# Create resource (POST)
class ResourceCreate(ResourceBase):
    consumed_by: UUID

# Update resource (PUT)
class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    filetype: Optional[FileTypeEnum] = None
    filepath: Optional[str] = None
    size: Optional[int] = None
    timestamp: Optional[datetime] = None
    consumed_by: Optional[UUID] = None

# Get resource (GET)
class ResourceResponse(ResourceBase):
    id: UUID
    consumed_by: UUID
    agent: AgentResponse

    model_config = {
        "from_attributes": True
    }
