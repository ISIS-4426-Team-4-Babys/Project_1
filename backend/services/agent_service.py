from errors.agent_errors import AgentNotFoundError
from schemas.agent_schema import AgentCreate, AgentUpdate, AgentResponse
from errors.db_errors import IntegrityConstraintError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from models.agent_model import Agent
import logging

logger = logging.getLogger("app.services.agent")

# Create agent (POST)
def create_agent(db: Session, agent_data: AgentCreate):
    logger.info("Creating new agent with name=%s", agent_data.name)
    
    agent = Agent(
        name = agent_data.name,
        description = agent_data.description,
        is_working = agent_data.is_working,
        system_prompt = agent_data.system_prompt,
        model = agent_data.model,
        language = agent_data.language,
        retrieval_k = agent_data.retrieval_k,
        associated_course_id = agent_data.associated_course
    )
    
    try:
        db.add(agent)
        db.commit()
        db.refresh(agent)
        logger.info("Agent created successfully with id=%s", agent.id)
        return agent
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when creating agent: %s", e)
        raise IntegrityConstraintError("Create Agent")
    

# Get all agents (GET)
def get_agents(db: Session):
    logger.debug("Fetching all agents")
    return db.query(Agent).options(selectinload(Agent.associated_course)).all()


# Get agent by ID (GET)
def get_agent_by_id(db: Session, agent_id: int):
    logger.debug("Fetching agent with id=%s", agent_id)
    agent = db.query(Agent).options(selectinload(Agent.associated_course)).filter(Agent.id == agent_id).first()
    if not agent:
        raise AgentNotFoundError("id", agent_id)
    return agent


# Update agent (PUT)
def update_agent(db: Session, agent_id: int, agent_data: AgentUpdate):
    logger.info("Updating agent with id=%s", agent_id)
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        raise AgentNotFoundError("id", agent_id)

    for key, value in agent_data.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)

    try:
        db.commit()
        db.refresh(agent)
        logger.info("Agent updated successfully with id=%s", agent.id)
        return agent
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when updating agent: %s", e)
        raise IntegrityConstraintError("Update Agent")

# Delete agent (DELETE)
def delete_agent(db: Session, agent_id: int):
    logger.info("Deleting agent with id=%s", agent_id)
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        raise AgentNotFoundError("id", agent_id)
    db.delete(agent)
    db.commit()
    logger.info("Agent deleted successfully with id=%s", agent.id)
    return agent