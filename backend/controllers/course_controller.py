from .responses.course_responses import create_course_responses, get_course_by_id_responses, update_course_responses, delete_course_responses, enroll_student_responses, unenroll_student_responses
from errors.course_errors import CourseNotFoundError, DuplicateCourseError, InvalidUserRoleError
from schemas.course_schema import CourseCreate, CourseUpdate, CourseResponse
from fastapi import APIRouter, Depends, HTTPException, status
from errors.db_errors import IntegrityConstraintError
from schemas.agent_schema import AgentResponse
from middlewares.jwt_auth import require_roles
from schemas.user_schema import UserResponse
from models.user_model import UserRole
from sqlalchemy.orm import Session
from config.database import get_db
from services.course_service import (
    create_course,
    get_courses,
    get_course_by_id,
    update_course,
    delete_course,
    enroll_student,
    unenroll_student,
    get_agents_in_course,
    get_students_in_course
)

router = APIRouter(prefix = "/courses", tags = ["Courses"])


# Create Course
@router.post("/", 
             response_model = CourseResponse, 
             status_code = status.HTTP_201_CREATED, 
             dependencies = [Depends(require_roles(UserRole.admin))],
             responses = create_course_responses)
def create_course_endpoint(course_data: CourseCreate, db: Session = Depends(get_db)):
    try:
        return create_course(db, course_data)
    except DuplicateCourseError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = str(e))


# Get All Courses
@router.get("/", 
            response_model = list[CourseResponse], 
            status_code = status.HTTP_200_OK, 
            dependencies = [Depends(require_roles(UserRole.admin))])
def get_courses_endpoint(db: Session = Depends(get_db)):
    return get_courses(db)


# Get Course by ID
@router.get("/{course_id}", 
            response_model = CourseResponse, 
            status_code = status.HTTP_200_OK, 
            dependencies = [Depends(require_roles(UserRole.admin))],
            responses = get_course_by_id_responses)
def get_course_by_id_endpoint(course_id: str, db: Session = Depends(get_db)):
    try:
        return get_course_by_id(db, course_id)
    except CourseNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))


# Update Course
@router.put("/{course_id}", 
            response_model = CourseResponse, 
            status_code = status.HTTP_200_OK, 
            dependencies = [Depends(require_roles(UserRole.admin))],
            responses = update_course_responses)
def update_course_endpoint(course_id: str, course_data: CourseUpdate, db: Session = Depends(get_db)):
    try:
        return update_course(db, course_id, course_data)
    except CourseNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))
    except DuplicateCourseError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = str(e))


# Delete Course
@router.delete("/{course_id}", 
               response_model = CourseResponse, 
               status_code = status.HTTP_200_OK, 
               dependencies = [Depends(require_roles(UserRole.admin))],
               responses = delete_course_responses)
def delete_course_endpoint(course_id: str, db: Session = Depends(get_db)):
    try:
        return delete_course(db, course_id)
    except CourseNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))


# Enroll a student in a course
@router.post(
    "/{course_id}/students/{student_id}",
    response_model = CourseResponse,
    status_code = status.HTTP_200_OK,
    dependencies = [Depends(require_roles(UserRole.admin))],
    responses = enroll_student_responses
)
def enroll_student_endpoint(course_id: str, student_id: str, db: Session = Depends(get_db)):
    try:
        return enroll_student(db, course_id, student_id)
    except InvalidUserRoleError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except CourseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Unenroll a student from a course
@router.delete(
    "/{course_id}/students/{student_id}",
    response_model = CourseResponse,
    status_code = status.HTTP_200_OK,
    dependencies = [Depends(require_roles(UserRole.admin))],
    responses = unenroll_student_responses
)
def unenroll_student_endpoint(course_id: str, student_id: str, db: Session = Depends(get_db)):
    try:
        return unenroll_student(db, course_id, student_id)
    except InvalidUserRoleError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except CourseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Get all students enrolled in a course
@router.get(
    "/{course_id}/students",
    response_model = list[UserResponse],
    status_code = status.HTTP_200_OK,
    dependencies = [Depends(require_roles(UserRole.admin, UserRole.professor))]
)
def get_students_in_course_endpoint(course_id: str, db: Session = Depends(get_db)):
    return get_students_in_course(db, course_id)


# Get all agents associated with a course
@router.get(
    "/{course_id}/agents",
    response_model = list[AgentResponse],
    status_code = status.HTTP_200_OK,
    dependencies = [Depends(require_roles(UserRole.admin, UserRole.admin, UserRole.student))]
)
def get_agents_in_course_endpoint(course_id: str, db: Session = Depends(get_db)):
    return get_agents_in_course(db, course_id)