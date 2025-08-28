import logging
from uuid import UUID as UUID_t
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from errors.user_errors import (
    UserNotFoundError, DuplicateUserError, InvalidCredentialsError
)
from errors.db_errors import IntegrityConstraintError
from models.user_model import User
from schemas.user_schema import UserCreate, UserUpdate
from passlib.context import CryptContext

logger = logging.getLogger("app.services.user")
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------- helpers ----------
def _hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

# ---------- CRUD ----------
def create_user(db: Session, data: UserCreate):
    logger.info("Creating user email=%s", data.email)

    if db.query(User).filter(User.email == data.email).first():
        logger.warning("Duplicate email=%s", data.email)
        raise DuplicateUserError("email", data.email)
    if db.query(User).filter(User.name == data.name).first():
        logger.warning("Duplicate name=%s", data.name)
        raise DuplicateUserError("name", data.name)

    user = User(
        name=data.name,
        email=data.email,
        password=_hash_password(data.password),
        role=data.role,
        profile_image=data.profile_image
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("User created id=%s", user.id)
        return user
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError creating user: %s", str(e))
        raise IntegrityConstraintError("Create User")

def get_users(db: Session):
    logger.debug("Fetching all users")
    return db.query(User).all()

def get_user_by_id(db: Session, user_id: str | UUID_t):
    user = db.query(User).filter(User.id == str(user_id)).first()
    if not user:
        raise UserNotFoundError("id", str(user_id))
    return user

def get_user_by_email(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise UserNotFoundError("email", email)
    return user

def update_user(db: Session, user_id: str | UUID_t, data: UserUpdate):
    user = get_user_by_id(db, user_id)

    # Uniqueness checks
    if data.email and data.email != user.email:
        if db.query(User).filter(User.email == data.email).first():
            raise DuplicateUserError("email", data.email)
    if data.name and data.name != user.name:
        if db.query(User).filter(User.name == data.name).first():
            raise DuplicateUserError("name", data.name)

    payload = data.model_dump(exclude_unset=True)
    if "password" in payload and payload["password"]:
        payload["password"] = _hash_password(payload["password"])
    elif "password" in payload:
        payload.pop("password")

    for k, v in payload.items():
        setattr(user, k, v)

    try:
        db.commit()
        db.refresh(user)
        logger.info("User updated id=%s", user.id)
        return user
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError updating user: %s", str(e))
        raise IntegrityConstraintError("Update User")

def delete_user(db: Session, user_id: str | UUID_t):
    user = get_user_by_id(db, user_id)
    db.delete(user)
    db.commit()
    logger.info("User deleted id=%s", user_id)
    return user

# ---------- Auth ----------
def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not _verify_password(password, user.password):
        logger.warning("Invalid credentials email=%s", email)
        raise InvalidCredentialsError()
    return user
