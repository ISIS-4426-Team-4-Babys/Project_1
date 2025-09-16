from controllers import agent_controller, auth_controller, course_controller, resource_controller, user_controller
from config.logging import setup_logging
from config.rabbitmq import RabbitMQ
from fastapi import FastAPI

# Set custom logger for application
logger = setup_logging()

app = FastAPI()

rabbitmq = RabbitMQ()

# Include routers
app.include_router(agent_controller.router)
app.include_router(auth_controller.router)
app.include_router(course_controller.router)
app.include_router(resource_controller.router)
app.include_router(user_controller.router)
