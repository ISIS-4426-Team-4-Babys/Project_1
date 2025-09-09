import logging
import sys


def setup_logging():
    # Centralized configuration
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers = [
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Logging queries in production
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    return logging.getLogger("app")