from schemas.course_schema import CourseCreate, CourseUpdate, CourseResponse
from errors.course_errors import CourseNotFoundError, DuplicateCourseError
from fastapi import APIRouter, Depends, HTTPException, status
from errors.db_errors import IntegrityConstraintError
from sqlalchemy.orm import Session
from config.database import get_db
from services.course_service import (
    create_course,
    get_courses,
    get_course_by_id,
    update_course,
    delete_course,
)

router = APIRouter(prefix = "/courses", tags = ["Courses"])

# Create Course
@router.post("/", response_model = CourseResponse, status_code = status.HTTP_201_CREATED)
def create_course_endpoint(course_data: CourseCreate, db: Session = Depends(get_db)):
    try:
        return create_course(db, course_data)
    except DuplicateCourseError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = str(e))


# Get All Courses
@router.get("/", response_model = list[CourseResponse], status_code = status.HTTP_200_OK)
def get_courses_endpoint(db: Session = Depends(get_db)):
    return get_courses(db)


# Get Course by ID
@router.get("/{course_id}", response_model = CourseResponse, status_code = status.HTTP_200_OK)
def get_course_by_id_endpoint(course_id: str, db: Session = Depends(get_db)):
    try:
        return get_course_by_id(db, course_id)
    except CourseNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))


# Update Course
@router.put("/{course_id}", response_model = CourseResponse, status_code = status.HTTP_200_OK)
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
@router.delete("/{course_id}", response_model = CourseResponse, status_code = status.HTTP_200_OK)
def delete_course_endpoint(course_id: str, db: Session = Depends(get_db)):
    try:
        return delete_course(db, course_id)
    except CourseNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))

