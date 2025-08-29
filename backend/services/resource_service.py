from errors.resource_errors import ResourceNotFoundError, DuplicateResourceError, InvalidFileTypeError, FileSizeError
from schemas.resource_schema import ResourceCreate, ResourceUpdate
from errors.db_errors import IntegrityConstraintError
from sqlalchemy.orm import Session, selectinload
from models.resource_model import Resource
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger("app.services.resource")

# Create resource (POST)
def create_resource(db: Session, resource_data: ResourceCreate):
    logger.info("Creating new resource with name=%s", resource_data.name)
    
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
    MAX_FILE_SIZE = 100 * 1024 * 1024  
    if resource_data.size > MAX_FILE_SIZE:
        logger.warning("Resource with name=%s exceeds max file size", resource_data.name)
        raise FileSizeError(resource_data.size, MAX_FILE_SIZE)
    
    resource = Resource(
        id = str(resource_data.id),
        name = resource_data.name,
        filetype = resource_data.filetype,
        size = resource_data.size,
        timestamp = resource_data.timestamp,
        consumed_by = resource_data.consumed_by
    )

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
    resource = db.query(Resource).options(selectinload(Resource.agent)).filter(Resource.id == resource.id).first()
    if not resource:
        raise ResourceNotFoundError("id", resource_id)
    return resource


# Update resource (PUT)
def update_resource(db: Session, resource_id: str, resource_data: ResourceUpdate):
    logger.info("Updating resource id=%s", resource_id)
    resource = get_resource_by_id(db, resource_id)
    
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
    MAX_FILE_SIZE = 100 * 1024 * 1024  
    if resource_data.size > MAX_FILE_SIZE:
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
    if not resource:
        logger.warning("Resource not found id=%s", resource_id)
        raise ResourceNotFoundError("id", resource_id)

    db.delete(resource)
    db.commit()
    logger.info("Resource deleted successfully id=%s", resource_id)
    return resource
