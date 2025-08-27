from sqlalchemy import Column, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from config.database import Base
import enum

# Define role enumeration
class UserRole(enum.Enum):
    student = "student"
    professor = "professor"
    admin = "admin"

# Define user model
class User(Base):
    __tablename__ = "users"

    name = Column(String(100), unique = True, nullable = False)
    email = Column(String(100), unique = True, nullable = False)
    password = Column(Text, nullable = False)
    role = Column(Enum(UserRole), nullable = False)
    profile_image = Column(Text)
