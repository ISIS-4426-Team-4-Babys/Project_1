from config.logging import setup_logging
from controllers import course_controller, resource_controller
from fastapi import FastAPI

# Set custom logger for application
logger = setup_logging()

app = FastAPI()

# Include routers
app.include_router(course_controller.router)
app.include_router(resource_controller.router)
