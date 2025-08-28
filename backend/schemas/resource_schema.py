from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from models.resource_model import FileTypeEnum

# Define resource base schema
class ResourceBase(BaseModel):
    name: str
    filetype: FileTypeEnum
    size: int
    timestamp: datetime
    consumed_by: UUID

# Create resource (POST)
class ResourceCreate(ResourceBase):
    id: UUID

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

    model_config = {
        "from_attributes": True
    }
