from .responses.user_responses import create_user_responses, get_user_by_id_responses, get_user_by_email_responses, update_user_responses, delete_user_responses, student_courses_responses, professor_courses_responses
from errors.user_errors import UserNotFoundError, DuplicateUserError, InvalidUserRoleError
from schemas.user_schema import UserCreate, UserUpdate, UserResponse
from fastapi import APIRouter, Depends, HTTPException, status
from errors.db_errors import IntegrityConstraintError
from schemas.course_schema import CourseResponse
from middlewares.jwt_auth import require_roles
from models.user_model import UserRole
from sqlalchemy.orm import Session
from config.database import get_db
from services.user_service import (
    create_user, 
    get_users, 
    get_user_by_id, 
    get_user_by_email,
    update_user, 
    delete_user,
    get_courses_for_professor,
    get_courses_for_student
)

router = APIRouter(prefix="/users", tags=["Users"])


# Create User Admin Only
@router.post("/", 
             response_model = UserResponse, 
             status_code = status.HTTP_201_CREATED, 
             dependencies = [Depends(require_roles(UserRole.admin))],
             responses = create_user_responses,)
def create_user_endpoint(data: UserCreate, db: Session = Depends(get_db)):
    try:
        return create_user(db, data)
    except DuplicateUserError as e:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# Get Users Admin Only
@router.get("/", 
            response_model = list[UserResponse], 
            dependencies = [Depends(require_roles(UserRole.admin))])
def get_users_endpoint(db: Session = Depends(get_db)):
    return get_users(db)


# Get User by Id
@router.get("/{user_id}", 
            response_model = UserResponse, 
            dependencies = [Depends(require_roles(UserRole.admin, UserRole.professor, UserRole.admin))],
            responses = get_user_by_id_responses)
def get_user_by_id_endpoint(user_id: str, db: Session = Depends(get_db)):
    try:
        return get_user_by_id(db, user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Get user by email admin only
@router.get("/email/{email}", 
            response_model = UserResponse,
            dependencies = [Depends(require_roles(UserRole.admin))],
            responses = get_user_by_email_responses)
def get_user_by_email_endpoint(email: str, db: Session = Depends(get_db)):
    try:
        return get_user_by_email(db, email)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Update user admin only
@router.put("/{user_id}", 
            response_model = UserResponse, 
            dependencies = [Depends(require_roles(UserRole.admin))],
            responses = update_user_responses)
def update_user_endpoint(user_id: str, data: UserUpdate, db: Session = Depends(get_db)):
    try:
        return update_user(db, user_id, data)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateUserError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# Delete user admin only
@router.delete("/{user_id}", 
               response_model = UserResponse,
               dependencies = [Depends(require_roles(UserRole.admin))],
               responses = delete_user_responses)
def delete_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    try:
        return delete_user(db, user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Get all courses a student is enrolled in
@router.get(
    "/student/{student_id}",
    response_model = list[CourseResponse],
    status_code = status.HTTP_200_OK,
    dependencies = [Depends(require_roles(UserRole.admin, UserRole.student))],
    responses = student_courses_responses
)
def get_courses_for_student_endpoint(student_id: str, db: Session = Depends(get_db)):
    try:
        return get_courses_for_student(db, student_id)
    except InvalidUserRoleError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))


# Get all courses taught by a professor
@router.get(
    "/professor/{professor_id}",
    response_model = list[CourseResponse],
    status_code = status.HTTP_200_OK,
    dependencies = [Depends(require_roles(UserRole.admin, UserRole.professor))],
    responses = professor_courses_responses
)
def get_courses_for_professor_endpoint(professor_id: str, db: Session = Depends(get_db)):
    try:
        return get_courses_for_professor(db, professor_id)
    except InvalidUserRoleError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))