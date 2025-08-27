from sqlalchemy import Column, String, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from config.database import Base
import enum

# Define department enumeration
class CourseDepartment(enum.Enum):
    disc = "systems and computing engineering"

# Define course model
class Course(Base):
    __tablename__ = "courses"

    name = Column(String(100), unique = True, nullable = False)
    code = Column(String(20), unique = True, nullable = False)
    department = Column(Enum(CourseDepartment), nullable=False) 
    description = Column(Text, nullable = False)
    taught_by = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)

    teacher = relationship("User", backref = "courses_taught")
    students = relationship("User", secondary = "courses_students", backref = "courses_taken")
