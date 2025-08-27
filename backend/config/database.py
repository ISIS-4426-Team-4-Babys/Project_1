from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
import logging
import os

logger = logging.getLogger("app.config.db")

# Get environment variables
DB_USER = os.getenv("DB_USER","4-babys")
DB_PASSWORD = os.getenv("DB_PASSWORD","maluma")
DB_NAME = os.getenv("DB_NAME","agents-db")
DB_HOST = os.getenv("DB_HOST","localhost")
DB_PORT = os.getenv("DB_PORT","8082")

# Connection URL
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.info("Creating database engine...")
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)
Base = declarative_base()

logger.info("Database engine and session configured successfully")

# Dependency for use FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error: %s", e)
        raise
    finally:
        db.close()
        logger.debug("Database session closed")