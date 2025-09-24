from schemas.agent_schema import AgentCreate, AgentUpdate
from errors.db_errors import IntegrityConstraintError
from errors.course_errors import CourseNotFoundError
from errors.agent_errors import AgentNotFoundError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from models.course_model import Course
from models.agent_model import Agent
from config.rabbitmq import RabbitMQ
import logging
import anyio
import json
import os

logger = logging.getLogger("app.services.agent")
UPLOAD_DIR = "backend/prompts"

rabbitmq = RabbitMQ()


# Create agent (POST)
async def create_agent(db: Session, agent_data: AgentCreate):
    logger.info("Creating new agent with name=%s", agent_data.name)
    
    # Verify associated course
    existing_course = db.query(Course).filter(Course.id == agent_data.associated_course).first()
    if not existing_course:
        logger.warning("Associated course not found id=%s", agent_data.associated_course)
        raise CourseNotFoundError("id", agent_data.associated_course)

    agent = Agent(
        name = agent_data.name,
        description = agent_data.description,
        is_working = agent_data.is_working,
        system_prompt = agent_data.system_prompt,
        model = agent_data.model,
        language = agent_data.language,
        retrieval_k = agent_data.retrieval_k,
        associated_course = agent_data.associated_course
    )
    
    try:
        db.add(agent)
        db.commit()
        db.refresh(agent)
        agent = db.query(Agent).options(selectinload(Agent.course)).filter(Agent.id == agent.id).first()
        logger.info("Agent created successfully id=%s", agent.id)
        
        agent_id = agent.id
        agent_dir =  os.path.join(UPLOAD_DIR, str(agent_id))
        os.makedirs(agent_dir, exist_ok = True)
        filepath = os.path.join(agent_dir, "prompt.txt")

        async with await anyio.open_file(filepath, "w", encoding = "utf-8") as f:
            await f.write(agent.system_prompt)

        message = {
            "filepath": filepath
        }

        await rabbitmq.publish("prompt", json.dumps(message))
        logger.info("Prompt path published in prompt topic")

        return agent
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when creating agent: %s", str(e))
        raise IntegrityConstraintError("Create Agent")
    

# Get all agents (GET)
def get_agents(db: Session):
    logger.debug("Fetching all agents")
    return db.query(Agent).options(selectinload(Agent.course), selectinload(Agent.resources)).all()


# Get agent by ID (GET)
def get_agent_by_id(db: Session, agent_id: str):
    logger.debug("Fetching agent by id=%s", agent_id)
    agent = db.query(Agent).options(selectinload(Agent.course), selectinload(Agent.resources)).filter(Agent.id == agent_id).first()
    if not agent:
        raise AgentNotFoundError("id", agent_id)
    return agent


# Update agent (PUT)
def update_agent(db: Session, agent_id: str, agent_data: AgentUpdate):
    logger.info("Updating agent id=%s", agent_id)
    agent = get_agent_by_id(db, agent_id)
    
    if agent_data.associated_course is not None:
        existing_course = db.query(Course).filter(Course.id == agent_data.associated_course).first()
        if not existing_course:
            logger.warning("Associated course not found id=%s", agent_data.associated_course)
            raise CourseNotFoundError("id", agent_data.associated_course)

    for key, value in agent_data.model_dump(exclude_unset = True).items():
        setattr(agent, key, value)

    try:
        db.commit()
        db.refresh(agent)
        agent = db.query(Agent).options(selectinload(Agent.course)).filter(Agent.id == agent.id).first()
        logger.info("Agent updated successfully id=%s", agent.id)
        return agent
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when updating agent: %s", str(e))
        raise IntegrityConstraintError("Update Agent")


# Delete agent (DELETE)
def delete_agent(db: Session, agent_id: str):
    logger.info("Deleting agent id=%s", agent_id)
    agent = get_agent_by_id(db, agent_id)
    db.delete(agent)
    db.commit()
    logger.info("Agent deleted successfully id=%s", agent_id)
    return agent


# Get all resources for an agent (GET)
def get_resources_for_agent(db: Session, agent_id: str):
    logger.debug("Fetching resources for agent id=%s", agent_id)
    agent = get_agent_by_id(db, agent_id)
    logger.info("Found %s resources for agent id=%s", len(agent.resources), agent_id)
    return agent.resources