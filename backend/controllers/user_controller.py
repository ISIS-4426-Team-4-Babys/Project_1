from schemas.user_schema import UserCreate, UserUpdate, UserResponse
from errors.user_errors import UserNotFoundError, DuplicateUserError
from fastapi import APIRouter, Depends, HTTPException, status
from errors.db_errors import IntegrityConstraintError
from middlewares.jwt_auth import require_roles
from models.user_model import UserRole
from sqlalchemy.orm import Session
from config.database import get_db
from services.user_service import (
    create_user, 
    get_users, 
    get_user_by_id, 
    get_user_by_email,
    update_user, delete_user
)

router = APIRouter(prefix="/users", tags=["Users"])


# Create User Admin Only
@router.post("/", 
             response_model = UserResponse, 
             status_code = status.HTTP_201_CREATED, 
             dependencies = [Depends(require_roles(UserRole.admin))])
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
            dependencies = [Depends(require_roles(UserRole.admin, UserRole.professor, UserRole.student))])
def get_user_by_id_endpoint(user_id: str, db: Session = Depends(get_db)):
    try:
        return get_user_by_id(db, user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Get user by email admin only
@router.get("/email/{email}", 
            response_model = UserResponse,
            dependencies = [Depends(require_roles(UserRole.admin))])
def get_user_by_email_endpoint(email: str, db: Session = Depends(get_db)):
    try:
        return get_user_by_email(db, email)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Update user admin only
@router.put("/{user_id}", 
            response_model = UserResponse, 
            dependencies = [Depends(require_roles(UserRole.admin))])
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
               dependencies = [Depends(require_roles(UserRole.admin))])
def delete_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    try:
        return delete_user(db, user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
