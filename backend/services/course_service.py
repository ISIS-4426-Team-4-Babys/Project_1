from errors.course_errors import CourseNotFoundError, DuplicateCourseError, InvalidUserRoleError
from schemas.course_schema import CourseCreate, CourseUpdate
from errors.db_errors import IntegrityConstraintError
from sqlalchemy.orm import Session, selectinload
from services.user_service import get_user_by_id
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
    return db.query(Course).options(selectinload(Course.teacher), selectinload(Course.students), selectinload(Course.agents)).all()


# Get course by id (GET)
def get_course_by_id(db: Session, course_id: str):
    logger.debug("Fetching course by id=%s", course_id)
    course = db.query(Course).options(selectinload(Course.teacher), selectinload(Course.students), selectinload(Course.agents)).filter(Course.id == course_id).first()
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


# Enroll a student in a course (POST)
def enroll_student(db: Session, course_id: str, student_id: str):
    logger.info("Enrolling user id=%s with course id=%s", student_id, course_id)
    course = get_course_by_id(db, course_id)
    student = get_user_by_id(db, student_id)

    # Verify student role
    if student.role != UserRole.student:
        logger.warning("User id=%s is not a student (role=%s)", student_id, student.role)
        raise InvalidUserRoleError(student.role, "student")

    # Verify that the student isnt enrolled in the course
    if student in course.students:
        logger.info("Student id=%s is already enrolled in course id=%s", student_id, course_id)
        return course  

    # Enroll student
    course.students.append(student)

    try:
        db.commit()
        db.refresh(course)
        course = db.query(Course).options(selectinload(Course.students)).filter(Course.id == course.id).first()
        logger.info("Student id=%s enrolled successfully in course id=%s", student_id, course_id)
        return course
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when enrolling student: %s", str(e))
        raise IntegrityConstraintError("Enroll Student")


# Unenroll a student from a course (DELETE)
def unenroll_student(db: Session, course_id: str, student_id: str):
    logger.info("Unenrolling user id=%s from course id=%s", student_id, course_id)

    course = get_course_by_id(db, course_id)
    student = get_user_by_id(db, student_id)

    # Verify student role
    if student.role != UserRole.student:
        logger.warning("User id=%s is not a student (role=%s)", student_id, student.role)
        raise InvalidUserRoleError(student.role, "student")

    # Verify the student is enrolled in the course
    if student not in course.students:
        logger.info("Student id=%s is not enrolled in course id=%s", student_id, course_id)
        return course 

    # Remove student
    course.students.remove(student)

    try:
        db.commit()
        db.refresh(course)
        course = db.query(Course).options(selectinload(Course.students)).filter(Course.id == course.id).first()
        logger.info("Student id=%s unenrolled successfully from course id=%s", student_id, course_id)
        return course
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when unenrolling student: %s", str(e))
        raise IntegrityConstraintError("Unenroll Student")


# Get all students enrolled in a course (GET)
def get_students_in_course(db: Session, course_id: str):
    logger.debug("Fetching students for course id=%s", course_id)
    course = get_course_by_id(db, course_id)
    logger.info("Found %s students enrolled in course id=%s", len(course.students), course_id)
    return course.students


# Get all agents associated with a course (GET)
def get_agents_in_course(db: Session, course_id: str):
    logger.debug("Fetching agents for course id=%s", course_id)
    course = get_course_by_id(db, course_id)
    logger.info("Found %s agents associated with course id=%s", len(course.agents), course_id)
    return course.agents