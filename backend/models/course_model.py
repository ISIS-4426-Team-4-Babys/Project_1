from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from config.database import Base
import enum
import uuid

# Define course model
class Course(Base):
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name = Column(String(100), unique = True, nullable = False)
    code = Column(String(20), unique = True, nullable = False)
    department = Column(String(100), nullable = False) 
    description = Column(Text, nullable = False)
    taught_by = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)

    teacher = relationship("User", back_populates = "courses_taught")
    students = relationship("User", secondary = "courses_students", back_populates = "courses_taken")
    agents = relationship("Agent", back_populates = "course", cascade = "all, delete-orphan")


