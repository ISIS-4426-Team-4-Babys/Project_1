from config.logging import setup_logging
from controllers import course_controller
from fastapi import FastAPI

# Set custom logger for application
logger = setup_logging()

app = FastAPI()

app.include_router(course_controller.router)
