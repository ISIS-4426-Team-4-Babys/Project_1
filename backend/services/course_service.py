from errors.course_errors import CourseNotFoundError, DuplicateCourseError
from schemas.course_schema import CourseCreate, CourseUpdate
from errors.db_errors import IntegrityConstraintError
from sqlalchemy.orm import Session, selectinload
from errors.user_errors import UserNotFoundError
from models.user_model import User, UserRole
from sqlalchemy.exc import IntegrityError
from models.course_model import Course
import logging

logger = logging.getLogger("app.services.course")

# Create course (POST)
def create_course(db: Session, course_data: CourseCreate):
    logger.info("Creating new course with code=%s", course_data.code)

    # Check that there is no course with the same code
    existing_code = db.query(Course).filter(Course.code == course_data.code).first()
    if existing_code:
        logger.warning("Course with code=%s already exists", course_data.code)
        raise DuplicateCourseError("code", course_data.code)

    # Check that there is no course with the same name
    existing_name = db.query(Course).filter(Course.name == course_data.name).first()
    if existing_name:
        logger.warning("Course with name=%s already exists", course_data.name)
        raise DuplicateCourseError("name", course_data.name)
    
    # Check that the teacher exist
    existing_teacher = db.query(User).filter(User.id == course_data.taught_by, User.role == UserRole.professor).first()
    if not existing_teacher:
        logger.warning("Assigned teacher not found or not a professor id=%s", course_data.taught_by)
        raise UserNotFoundError("id", course_data.taught_by)

    course = Course(
        name = course_data.name,
        code = course_data.code,
        department = course_data.department,
        description = course_data.description,
        taught_by = course_data.taught_by,
    )

    try: 
        db.add(course)
        db.commit()
        db.refresh(course)
        course = db.query(Course).options(selectinload(Course.teacher)).filter(Course.id == course.id).first()
        logger.info("Course created successfully id=%s", course.id)
        return course
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when creating course: %s", str(e))
        raise IntegrityConstraintError("Create Course")


# Get all courses (GET)
def get_courses(db: Session):
    logger.debug("Fetching all courses")
    return db.query(Course).options(selectinload(Course.teacher)).all()


# Get course by id (GET)
def get_course_by_id(db: Session, course_id: str):
    logger.debug("Fetching course by id=%s", course_id)
    course = db.query(Course).options(selectinload(Course.teacher)).filter(Course.id == course_id).first()
    if not course:
        raise CourseNotFoundError("id", course_id)
    return course


# Update course (PUT)
def update_course(db: Session, course_id: str, course_data: CourseUpdate):
    logger.info("Updating course id=%s", course_id)
    course = get_course_by_id(db, course_id)

    # Check that there is no course with the same code
    if course_data.code and db.query(Course).filter(Course.code == course_data.code, Course.id != course_id).first():
        logger.warning("Course with code=%s already exists", course_data.code)
        raise DuplicateCourseError("code", course_data.code)

    # Check that there is no course with the same name
    if course_data.name and db.query(Course).filter(Course.name == course_data.name, Course.id != course_id).first():
        logger.warning("Course with name=%s already exists", course_data.name)
        raise DuplicateCourseError("name", course_data.name)
    
    # Check that the teacher exist
    if course_data.taught_by and db.query(User).filter(User.id == course_data.taught_by, User.role == UserRole.professor).first():
        logger.warning("Assigned teacher not found or not a professor id=%s", course_data.taught_by)
        raise UserNotFoundError("id", course_data.taught_by)

    for key, value in course_data.model_dump(exclude_unset = True).items():
        setattr(course, key, value)

    try:
        db.commit()
        db.refresh(course)
        course = db.query(Course).options(selectinload(Course.teacher)).filter(Course.id == course.id).first()
        logger.info("Course updated successfully id=%s", course.id)
        return course
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when creating course: %s", str(e))
        raise IntegrityConstraintError("Update Course")


# Delete course (DELETE)
def delete_course(db: Session, course_id: str):
    logger.info("Deleting course id=%s", course_id)
    course = get_course_by_id(db, course_id)
    db.delete(course)
    db.commit()
    logger.info("Course deleted successfully id=%s", course_id)
    return course