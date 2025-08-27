# Import all models here to ensure that SQLAlchemy can resolve relationships
# between models defined in separate files. 
# Using string references in `relationship()` requires that all classes 
# be registered with the same Base before the mappers are configured.
# This also prevents circular import issues and allows `Base.metadata.create_all()`
# to correctly create all tables.

from .course_student_model import CourseStudent
from .resource_model import Resource
from .course_model import Course
from .agent_model import Agent
from .user_model import User