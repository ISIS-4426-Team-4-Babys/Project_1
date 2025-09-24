from errors.resource_errors import ResourceNotFoundError, DuplicateResourceError, FileSizeError, FileDeletionError, FolderDeletionError
from errors.db_errors import IntegrityConstraintError
from schemas.resource_schema import ResourceCreate
from errors.agent_errors import AgentNotFoundError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from models.resource_model import Resource
from config.rabbitmq import RabbitMQ
from models.agent_model import Agent
from fastapi import UploadFile
import logging
import shutil
import anyio
import json
import os

logger = logging.getLogger("app.services.resource")
MAX_FILE_SIZE = 100 * 1024 * 1024  
UPLOAD_DIR = "backend/data"

rabbitmq = RabbitMQ()

def copy_sync(src_fileobj, dst_path: str):
    dst_dir = os.path.dirname(dst_path)
    os.makedirs(dst_dir, exist_ok=True)
    with open(dst_path, "wb") as out:
        shutil.copyfileobj(src_fileobj, out)
        out.flush()

# Create resource (POST)
async def create_resource(db: Session, resource_data: ResourceCreate, file: UploadFile):
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
    
    # Create agent folder
    agent_dir = os.path.join(UPLOAD_DIR, str(resource_data.consumed_by))
    final_path = os.path.join(agent_dir, file.filename)
    tmp_path = os.path.join(agent_dir, f".{file.filename}.part")  

    try:
        try:
            await file.seek(0)
        except Exception:
            pass
        
        await anyio.to_thread.run_sync(copy_sync, file.file, tmp_path)

        file_size = os.path.getsize(tmp_path)
        if file_size > MAX_FILE_SIZE:
            try:
                os.remove(tmp_path)
            except FileNotFoundError:
                pass
            logger.warning("Resource with name=%s exceeds max file size", resource_data.name)
            raise FileSizeError(file_size, MAX_FILE_SIZE)

        # Rename atómico a nombre final
        os.replace(tmp_path, final_path)

    except Exception as e:
        # Limpieza ante error
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        logger.error("Error while saving file: %s", e)
        raise
    

    # Update data in the schema
    resource_data.filepath = final_path
    resource_data.size = file_size

    # Get total document information
    total_docs = resource_data.total_docs

    # Create model
    resource = Resource(**resource_data.model_dump(exclude = {"total_docs"}))

    # Save in DB first
    try:
        db.add(resource)
        db.commit()
        db.refresh(resource)
        resource = db.query(Resource).options(selectinload(Resource.agent)).filter(Resource.id == resource.id).first()
    
    except IntegrityError as e:
        db.rollback()
        logger.error("IntegrityError when creating resource: %s", str(e))
        raise IntegrityConstraintError("Create Resource")

    # Send to RabbitMQ
    message = {
        "filepath": resource.filepath,
        "total_docs": total_docs
    }
    
    await rabbitmq.publish("files", json.dumps(message))
    logger.info("Resource published in files topic")

    # Return full resoruce with agent loaded
    logger.info("Resource created successfully id=%s", resource.id)
    return resource




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


# Delete resource (DELETE)
def delete_resource(db: Session, resource_id: str):
    logger.info("Deleting resource id=%s", resource_id)
    resource = get_resource_by_id(db, resource_id)

    # Delete resource using filepath
    if resource.filepath and os.path.exists(resource.filepath):
        try:
            os.remove(resource.filepath)
            logger.info("File deleted successfully path=%s", resource.filepath)
        except Exception as e:
            logger.error("Error deleting file path=%s: %s", resource.filepath, str(e))
            raise FileDeletionError(resource.filepath, str(e))
        
    db.delete(resource)
    db.commit()

    agent_dir = os.path.dirname(resource.filepath)
    try:
        if os.path.isdir(agent_dir) and not os.listdir(agent_dir):
            shutil.rmtree(agent_dir)
            logger.info("Agent folder deleted because it was empty path=%s", agent_dir)
    except Exception as e:
        logger.error("Error cleaning agent folder path=%s: %s", agent_dir, str(e))
        raise FolderDeletionError(agent_dir, str(e))

    logger.info("Resource deleted successfully id=%s", resource_id)
    return resource
