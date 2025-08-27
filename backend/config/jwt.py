import logging
import os

logger = logging.getLogger("app.config.jwt")

# Get environment variables
JWT_SECRET = os.getenv("JWT_SECRET","a")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM","a")
JWT_EXPIRATION_MINUTES = os.getenv("JWT_EXPIRATION_MINUTES","a")

if not JWT_SECRET:
    logger.fatal("JWT_SECRET is not set in environment")
    raise RuntimeError("JWT_SECRET missing")

logger.info("JWT configuration loaded successfully")