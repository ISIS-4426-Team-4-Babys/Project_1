from schemas.resource_schema import ResourceCreate, ResourceUpdate
from errors.db_errors import IntegrityConstraintError
from errors.resource_errors import ResourceNotFoundError, DuplicateResourceError, FileSizeError
from errors.agent_errors import AgentNotFoundError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from models.resource_model import Resource
from models.agent_model import Agent
from fastapi import UploadFile
import logging
import os

logger = logging.getLogger("app.services.resource")
MAX_FILE_SIZE = 100 * 1024 * 1024  
UPLOAD_DIR = "backend/data"

# Create resource (POST)
def create_resource(db: Session, resource_data: ResourceCreate, file: UploadFile):
    logger.info("Creating new resource with name=%s", resource_data.name)
    
    # Verify associated agent
    existing_agent = db.query(Agent).filter(Agent.id == resource_data.consumed_by).first()
    if not existing_agent:
        logger.warning("Associated agent not found id=%s", resource_data.consumed_by)
        raise AgentNotFoundError("id", resource_data.consumed_by)
    
    # Check if resource with same name already exists for the given agent
    existing_resource = (
        db.query(Resource)
        .filter(
            Resource.name == resource_data.name,
            Resource.consumed_by == resource_data.consumed_by  
        ).
        first()
    )
    if existing_resource:
        logger.warning("Resource with name=%s already consumed by the agent", resource_data.name)
        raise DuplicateResourceError(resource_data.name)
        
    # Validate max file size (100 MB)
    contents = file.file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE:
        logger.warning("Resource with name=%s exceeds max file size", resource_data.name)
        raise FileSizeError(file_size, MAX_FILE_SIZE)
    
    # Create agent folder
    agent_dir = os.path.join(UPLOAD_DIR, str(resource_data.consumed_by))
    os.makedirs(agent_dir, exist_ok = True)

    # Save file
    filepath = os.path.join(agent_dir, file.filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    # Update data in the schema
    resource_data.filepath = filepath
    resource_data.size = file_size

    # Create model
    resource = Resource(**resource_data.model_dump())

    try:
        db.add(resource)
        db.commit()
        db.refresh(resource)
        resource = db.query(Resource).options(selectinload(Resource.agent)).filter(Resource.id == resource.id).first()
        logger.info("Resource created successfully id=%s", resource.id)
        return resource
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when creating resource: %s", str(e))
        raise IntegrityConstraintError("Create Resource")


# Get all resources (GET)
def get_resources(db: Session):
    logger.debug("Fetching all resources")
    return db.query(Resource).options(selectinload(Resource.agent)).all()


# Get resource by id (GET)
def get_resource_by_id(db: Session, resource_id: str):
    logger.debug("Fetching resource by id=%s", resource_id)
    resource = db.query(Resource).options(selectinload(Resource.agent)).filter(Resource.id == resource_id).first()
    if not resource:
        raise ResourceNotFoundError("id", resource_id)
    return resource


# Update resource (PUT)
def update_resource(db: Session, resource_id: str, resource_data: ResourceUpdate):
    logger.info("Updating resource id=%s", resource_id)
    resource = get_resource_by_id(db, resource_id)
    
    # Verify associated agent if changed
    if resource_data.consumed_by is not None:
        existing_agent = db.query(Agent).filter(Agent.id == resource_data.consumed_by).first()
        if not existing_agent:
            logger.warning("Associated agent not found id=%s", resource_data.consumed_by)
            raise AgentNotFoundError("id", resource_data.consumed_by)
    
    # Check for duplicate resource for the agent
    if resource_data.name is not None and resource_data.consumed_by is not None:
        existing_resource = (
            db.query(Resource)
            .filter(Resource.name == resource_data.name, Resource.consumed_by == resource_data.consumed_by)
            .first()
        )
        if existing_resource and existing_resource.id != resource.id:
            logger.warning("Resource with name=%s already consumed by the agent", resource_data.name)
            raise DuplicateResourceError(resource_data.name)
        
    # Validate max file size
    if resource_data.size is not None and resource_data.size > MAX_FILE_SIZE:
        logger.warning("Resource with name=%s exceeds max file size", resource_data.name)
        raise FileSizeError(resource_data.size, MAX_FILE_SIZE)
    
    for key, value in resource_data.model_dump(exclude_unset = True).items():
        setattr(resource, key, value)

    try:
        db.commit()
        db.refresh(resource)
        logger.info("Resource updated successfully id=%s", resource.id)
        resource = db.query(Resource).options(selectinload(Resource.agent)).filter(Resource.id == resource.id).first()
        return resource
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when updating resource: %s", str(e))
        raise IntegrityConstraintError("Update Resource")


# Delete resource (DELETE)
def delete_resource(db: Session, resource_id: str):
    logger.info("Deleting resource id=%s", resource_id)
    resource = get_resource_by_id(db, resource_id)
    db.delete(resource)
    db.commit()
    logger.info("Resource deleted successfully id=%s", resource_id)
    return resource
