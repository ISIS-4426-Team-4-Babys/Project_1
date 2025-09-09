from sqlalchemy import Column, String, Text, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from config.database import Base
import enum
import uuid

# Define resource model
class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name = Column(String(100), nullable = False)
    filetype = Column(String(100), nullable = False)
    filepath = Column(Text, nullable = False)
    size = Column(Integer, nullable = False)
    timestamp = Column(TIMESTAMP, nullable = False)
    consumed_by = Column(UUID(as_uuid = True), ForeignKey("agents.id", ondelete = "CASCADE"), nullable = False)

    agent = relationship("Agent", back_populates="resources")

