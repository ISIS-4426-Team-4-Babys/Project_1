from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, ForeignKey
from config.database import Base

# Define courses student model
class CourseStudent(Base):
    __tablename__ = "courses_students"

    course_id = Column(UUID(as_uuid = True), ForeignKey("courses.id", ondelete = "CASCADE"), primary_key = True)
    student_id = Column(UUID(as_uuid = True), ForeignKey("users.id", ondelete = "CASCADE"), primary_key = True)
