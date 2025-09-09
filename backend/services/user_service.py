from errors.user_errors import UserNotFoundError, DuplicateUserError, InvalidCredentialsError, InvalidUserRoleError
from schemas.user_schema import UserCreate, UserUpdate
from errors.db_errors import IntegrityConstraintError
from sqlalchemy.orm import Session, selectinload
from models.user_model import User, UserRole
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
import logging


logger = logging.getLogger("app.services.user")
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated = "auto")


# Helpers to manage password securely
def _hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# Create user (POST)
def create_user(db: Session, data: UserCreate):
    logger.info("Creating user email=%s", data.email)

    # Check for duplicates
    existing_email = db.query(User).filter(User.email == data.email).first()
    if existing_email:
        logger.warning("User with email=%s alredy exist", data.email)
        raise DuplicateUserError("email", data.email)
    
    existing_name = db.query(User).filter(User.name == data.name).first()
    if existing_name:
        logger.warning("User with name=%s alredy exist", data.name)
        raise DuplicateUserError("name", data.name)

    user = User(
        name = data.name,
        email = data.email,
        password = _hash_password(data.password),
        role = data.role,
        profile_image = data.profile_image
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        user = db.query(User).filter(User.id == user.id).first()
        logger.info("User created successfully id=%s", user.id)
        return user
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError creating user: %s", str(e))
        raise IntegrityConstraintError("Create User")


# Get all users (GET)
def get_users(db: Session):
    logger.debug("Fetching all users")
    return db.query(User).options(selectinload(User.courses_taken), selectinload(User.courses_taught)).all()


# Get user by id (GET)
def get_user_by_id(db: Session, user_id: str):
    logger.debug("Fetching user by id=%s", user_id)
    user = db.query(User).options(selectinload(User.courses_taken), selectinload(User.courses_taught)).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError("id", str(user_id))
    return user


# Get user by email (GET)
def get_user_by_email(db: Session, user_email: str):
    logger.debug("Fetching user by email=%s", user_email)
    user = db.query(User).options(selectinload(User.courses_taken), selectinload(User.courses_taught)).filter(User.email == user_email).first()
    if not user:
        raise UserNotFoundError("email", user_email)
    return user


# Update user (PUT)
def update_user(db: Session, user_id: str, data: UserUpdate):
    logger.info("Updating user id=%s", user_id)
    user = get_user_by_id(db, user_id)

    # Uniqueness checks
    if data.email and db.query(User).filter(User.email == data.email).first():
        logger.warning("User with email=%s alredy exist", data.email)
        raise DuplicateUserError("email", data.email)
    
    if data.name and db.query(User).filter(User.name == data.name).first():
        logger.warning("User with name=%s alredy exist", data.name)
        raise DuplicateUserError("name", data.name)

    payload = data.model_dump(exclude_unset = True)
    if "password" in payload and payload["password"]:
        payload["password"] = _hash_password(payload["password"])
    elif "password" in payload:
        payload.pop("password")

    for k, v in payload.items():
        setattr(user, k, v)

    try:
        db.commit()
        db.refresh(user)
        user = db.query(User).filter(User.id == user.id).first()
        logger.info("User updated succesfully id=%s", user.id)
        return user
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError updating user: %s", str(e))
        raise IntegrityConstraintError("Update User")


# Delete course (DELETE)
def delete_user(db: Session, user_id: str):
    logger.info("Deleting user id=%s", user_id)
    user = get_user_by_id(db, user_id)
    db.delete(user)
    db.commit()
    logger.info("User deleted id=%s", user_id)
    return user


# Authenticate User (POST)
def authenticate_user(db: Session, user_email: str, password: str) -> User:
    logger.info("Authenticating user email=%s", user_email)
    user = get_user_by_email(db, user_email)
    if not user or not _verify_password(password, user.password):
        logger.warning("Invalid credentials email=%s", user_email)
        raise InvalidCredentialsError()
    return user


# Get all courses a student is enrolled in (GET)
def get_courses_for_student(db: Session, student_id: str):
    logger.debug("Fetching courses for student id=%s", student_id)
    student = get_user_by_id(db, student_id)

    if student.role != UserRole.student:
        logger.warning("User id=%s is not a student (role=%s)", student_id, student.role)
        raise InvalidUserRoleError(student.role, "student")

    logger.info("Found %s courses for student id=%s", len(student.courses_taken), student_id)
    return student.courses_taken


# Get all courses taught by a professor (GET)
def get_courses_for_professor(db: Session, professor_id: str):
    logger.debug("Fetching courses for professor id=%s", professor_id)
    professor = get_user_by_id(db, professor_id)

    if professor.role != UserRole.professor:
        logger.warning("User id=%s is not a teacher (role=%s)", professor_id, professor.role)
        raise InvalidUserRoleError(professor.role, "teacher")

    logger.info("Found %s courses for professor id=%s", len(professor.courses_taught), professor_id)
    return professor.courses_taught
