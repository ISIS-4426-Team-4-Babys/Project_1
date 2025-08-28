from sqlalchemy import Column, String, Text, Boolean, Integer, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from config.database import Base
import enum
import uuid

# Define language enumeration
class LanguageEnum(enum.Enum):
    es = "es"
    en = "en"

# Define agent model
class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name = Column(String(100), nullable = False)
    description = Column(Text, nullable = False)
    is_working = Column(Boolean, nullable = False)
    system_prompt = Column(Text, nullable = False)
    model = Column(String(100), nullable = False)
    language = Column(Enum(LanguageEnum), nullable = False)
    retrieval_k = Column(Integer, nullable = False)
    associated_course = Column(UUID(as_uuid = True), ForeignKey("courses.id", ondelete = "CASCADE"), nullable = False)
    
    course = relationship("Course", back_populates = "agents")
    resources = relationship("Resource", back_populates = "agent", cascade = "all, delete-orphan")
