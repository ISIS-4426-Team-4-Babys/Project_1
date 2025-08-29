from backend.middlewares.jwt_auth import require_roles
from backend.models.user_model import UserRole
from errors.resource_errors import ResourceNotFoundError, DuplicateResourceError, InvalidFileTypeError, FileSizeError
from schemas.resource_schema import ResourceCreate, ResourceUpdate, ResourceResponse
from fastapi import APIRouter, Depends, HTTPException, status
from errors.db_errors import IntegrityConstraintError
from services.resource_service import (
    create_resource,
    get_resources,
    get_resource_by_id,
    update_resource,
    delete_resource,
)
from sqlalchemy.orm import Session
from config.database import get_db

router = APIRouter(prefix="/resources", tags=["Resources"])

# Create Resource
@router.post("/", response_model = ResourceResponse, status_code = status.HTTP_201_CREATED, dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))])
def create_resource_endpoint(resource_data: ResourceCreate, db: Session = Depends(get_db)):
    try:
        return create_resource(db, resource_data)
    except DuplicateResourceError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except FileSizeError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = str(e))

# Get All Resources
@router.get("/", response_model = list[ResourceResponse], status_code = status.HTTP_200_OK, dependencies = [Depends(require_roles(UserRole.admin))])
def get_resources_endpoint(db: Session = Depends(get_db)):
    return get_resources(db)

# Get Resource by ID
@router.get("/{resource_id}", response_model = ResourceResponse, status_code = status.HTTP_200_OK, dependencies = [Depends(require_roles(UserRole.admin))])
def get_resource_by_id_endpoint(resource_id: str, db: Session = Depends(get_db)):
    try:
        return get_resource_by_id(db, resource_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))

# Update Resource
@router.put("/{resource_id}", response_model = ResourceResponse, status_code = status.HTTP_200_OK, dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))])
def update_resource_endpoint(resource_id: str, resource_data: ResourceUpdate, db: Session = Depends(get_db)):
    try:
        return update_resource(db, resource_id, resource_data)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))
    except DuplicateResourceError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except FileSizeError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    except IntegrityConstraintError as e:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = str(e))

# Delete Resource
@router.delete("/{resource_id}", response_model = ResourceResponse, status_code = status.HTTP_200_OK, dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))])
def delete_resource_endpoint(resource_id: str, db: Session = Depends(get_db)):
    try:
        return delete_resource(db, resource_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))
