from schemas.user_schema import LoginRequest, UserCreate, UserResponse, LoginResponse
from errors.user_errors import InvalidCredentialsError, DuplicateUserError
from .responses.auth_responses import register_responses, login_responses
from services.user_service import authenticate_user, create_user
from fastapi import APIRouter, Depends, HTTPException, status
from errors.db_errors import IntegrityConstraintError
from config.jwt import create_access_token
from sqlalchemy.orm import Session
from config.database import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


# Register new user
@router.post("/register", 
             response_model = UserResponse, 
             status_code = status.HTTP_201_CREATED,
             responses = register_responses)
def register_endpoint(data: UserCreate, db: Session = Depends(get_db)):
    try:
        return create_user(db, data)
    except DuplicateUserError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = str(e))


# Login user
@router.post("/login", 
             response_model = LoginResponse,
             responses = login_responses)
def login_endpoint(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, req.email, req.password)
        token = create_access_token(subject = str(user.id), extra_claims = {
            "role": user.role.value,
        })
        return LoginResponse(access_token = token, user = user)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = str(e))
