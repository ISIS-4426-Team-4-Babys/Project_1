from errors.resource_errors import ResourceNotFoundError, DuplicateResourceError, FileSizeError, FileDeletionError, FolderDeletionError
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from schemas.resource_schema import ResourceCreate, ResourceResponse
from middlewares.jwt_auth import require_roles
from errors.db_errors import IntegrityConstraintError
from models.user_model import UserRole
from sqlalchemy.orm import Session
from config.database import get_db
from datetime import datetime, timezone
from services.resource_service import (
    create_resource,
    get_resources,
    get_resource_by_id,
    delete_resource,
)


router = APIRouter(prefix="/resources", tags=["Resources"])


# Create Resource
@router.post("/", 
             response_model = ResourceResponse, 
             status_code = status.HTTP_201_CREATED, 
             dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))])
def create_resource_endpoint(db: Session = Depends(get_db), file: UploadFile = File(...), name: str = Form(...), consumed_by: str = Form(...)):
    
    resource_data = ResourceCreate(
        name = name,
        filetype = file.content_type,
        filepath = "",
        size = 0,
        timestamp = datetime.now(timezone.utc),
        consumed_by = consumed_by
    )
    
    try:
        return create_resource(db, resource_data, file)
    except DuplicateResourceError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except FileSizeError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = str(e))


# Get All Resources
@router.get("/", 
            response_model = list[ResourceResponse], 
            status_code = status.HTTP_200_OK, 
            dependencies = [Depends(require_roles(UserRole.admin))])
def get_resources_endpoint(db: Session = Depends(get_db)):
    return get_resources(db)


# Get Resource by ID
@router.get("/{resource_id}", 
            response_model = ResourceResponse, 
            status_code = status.HTTP_200_OK, 
            dependencies = [Depends(require_roles(UserRole.admin))])
def get_resource_by_id_endpoint(resource_id: str, db: Session = Depends(get_db)):
    try:
        return get_resource_by_id(db, resource_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))


# Delete Resource
@router.delete("/{resource_id}", 
               response_model = ResourceResponse, 
               status_code = status.HTTP_200_OK, 
               dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))])
def delete_resource_endpoint(resource_id: str, db: Session = Depends(get_db)):
    try:
        return delete_resource(db, resource_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))
    except FileDeletionError as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = str(e))
    except FolderDeletionError as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = str(e))