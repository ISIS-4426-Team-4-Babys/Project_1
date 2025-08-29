from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Optional
import logging
import os

logger = logging.getLogger("app.config.jwt")

# Get environment variables
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES"))

if not JWT_SECRET:
    logger.fatal("JWT_SECRET is not set in environment")
    raise RuntimeError("JWT_SECRET missing")

logger.info("JWT configuration loaded successfully")


def create_access_token(subject: str, extra_claims: Optional[dict] = None) -> str:

    logger.info("Creating JWT token ...")
    now = datetime.now(timezone.utc)
    to_encode = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes = JWT_EXPIRATION_MINUTES)).timestamp()),
        **(extra_claims or {}),
    }
    logger.info("JWT token created succesfully")
    return jwt.encode(to_encode, JWT_SECRET, algorithm = JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        logger.info("Decoding JWT token ...")
        return jwt.decode(token, JWT_SECRET, algorithms = [JWT_ALGORITHM])
    except JWTError as e:
        logger.info("Error decoding JWT token")
        raise ValueError(str(e))