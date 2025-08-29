from sqlalchemy import Column, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from config.database import Base
import enum
import uuid

# Define role enumeration
class UserRole(enum.Enum):
    student = "student"
    professor = "professor"
    admin = "admin"

# Define user model
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name = Column(String(100), unique = True, nullable = False)
    email = Column(String(100), unique = True, nullable = False)
    password = Column(Text, nullable = False)
    role = Column(Enum(UserRole), nullable = False)
    profile_image = Column(Text)

    courses_taught = relationship("Course", back_populates = "teacher")
    courses_taken = relationship("Course", secondary = "courses_students", back_populates = "students")

