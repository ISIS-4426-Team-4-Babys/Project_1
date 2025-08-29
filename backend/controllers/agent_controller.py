from schemas.agent_schema import AgentCreate, AgentUpdate, AgentResponse
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.resource_schema import ResourceResponse
from middlewares.jwt_auth import require_roles
from errors.db_errors import IntegrityConstraintError
from errors.agent_errors import AgentNotFoundError
from models.user_model import UserRole
from config.database import get_db 
from sqlalchemy.orm import Session
from services.agent_service import (
    get_resources_for_agent,
    create_agent,
    get_agents,
    get_agent_by_id,
    update_agent,
    delete_agent
)

router = APIRouter(prefix = "/agents", tags = ["Agents"])

# Create Agent
@router.post("/", 
             response_model = AgentResponse, 
             status_code = status.HTTP_201_CREATED, 
             dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))])
def create_agent_endpoint(agent_data: AgentCreate, db: Session = Depends(get_db)):
    try:
        agent = create_agent(db, agent_data)
        return agent
    except IntegrityConstraintError as e:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = str(e))


# Get All Agents
@router.get("/", 
            response_model = list[AgentResponse], 
            status_code = status.HTTP_200_OK, 
            dependencies = [Depends(require_roles(UserRole.admin))])
def get_agents_endpoint(db: Session = Depends(get_db)):
    return get_agents(db)


# Get Agent by ID
@router.get("/{agent_id}", 
            response_model = AgentResponse, 
            status_code = status.HTTP_200_OK, 
            dependencies = [Depends(require_roles(UserRole.admin))])
def get_agent_by_id_endpoint(agent_id: str, db: Session = Depends(get_db)):
    try:
        agent = get_agent_by_id(db, agent_id)
        return agent
    except AgentNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))
    

# Update Agent
@router.put("/{agent_id}", 
            response_model = AgentResponse, 
            status_code = status.HTTP_200_OK, 
            dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))])
def update_agent_endpoint(agent_id: str, agent_data: AgentUpdate, db: Session = Depends(get_db)):
    try:
        return update_agent(db, agent_id, agent_data)
    except AgentNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = str(e))


# Delete Agent
@router.delete("/{agent_id}", 
               response_model = AgentResponse, 
               status_code = status.HTTP_200_OK, 
               dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))])
def delete_agent_endpoint(agent_id: str, db: Session = Depends(get_db)):
    try:
        return delete_agent(db, agent_id)
    except AgentNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))


@router.get(
    "/resources",
    response_model = list[ResourceResponse],
    status_code = status.HTTP_200_OK,
    dependencies = [Depends(require_roles(UserRole.admin, UserRole.professor))]
)
def get_resources_for_agent_endpoint(agent_id: str, db: Session = Depends(get_db)):
    return get_resources_for_agent(db, agent_id)
