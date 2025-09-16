from errors.resource_errors import ResourceNotFoundError, DuplicateResourceError, FileSizeError, FileDeletionError, FolderDeletionError
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from schemas.resource_schema import ResourceCreate, ResourceResponse
from errors.db_errors import IntegrityConstraintError
from middlewares.jwt_auth import require_roles
from datetime import datetime, timezone
from models.user_model import UserRole
from sqlalchemy.orm import Session
from config.database import get_db
from services.resource_service import (
    create_resource,
    get_resources,
    get_resource_by_id,
    delete_resource,
)


router = APIRouter(prefix="/resources", tags=["Resources"])

create_resource_responses = {
    400: {
        "description": "Invalid resource payload (duplicate or file too large)",
        "content": {"application/json": {"examples": {
            "duplicate_resource": {"summary": "Duplicate resource name",
                                   "value": {"detail": r"Duplicate resource with name={name}"}},
            "file_too_large": {"summary": "File exceeds maximum size",
                               "value": {"detail": r"File size {size_mb}MB exceeds limit {limit_mb}MB"}},
        }}},
    },
    409: {
        "description": "Integrity constraint violation",
        "content": {"application/json": {"example":
            {"detail": r"Integrity constraint violation: {constraint_name}"}
        }},
    },
}

get_resource_by_id_responses = {
    404: {
        "description": "Resource not found",
        "content": {"application/json": {"example":
            {"detail": r"Resource with id={resource_id} not found"}
        }},
    },
}

delete_resource_responses = {
    404: {
        "description": "Resource not found",
        "content": {"application/json": {"example":
            {"detail": r"Resource with id={resource_id} not found"}
        }},
    },
    500: {
        "description": "Filesystem error while deleting underlying files/folders",
        "content": {"application/json": {"examples": {
            "file_delete_error": {"summary": "File deletion error",
                                  "value": {"detail": r"Could not delete file at {path}: {reason}"}},
            "folder_delete_error": {"summary": "Folder deletion error",
                                    "value": {"detail": r"Could not delete folder at {path}: {reason}"}},
        }}},
    },
}

# Create Resource
@router.post("/", 
             response_model = ResourceResponse, 
             status_code = status.HTTP_201_CREATED, 
             dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))],
             responses=create_resource_responses)
def create_resource_endpoint(db: Session = Depends(get_db), file: UploadFile = File(...), name: str = Form(...), consumed_by: str = Form(...), total_docs: str = Form(...)):
    
    resource_data = ResourceCreate(
        name = name,
        filetype = file.content_type,
        filepath = "",
        size = 0,
        timestamp = datetime.now(timezone.utc),
        consumed_by = consumed_by,
        total_docs = int(total_docs)
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
            dependencies = [Depends(require_roles(UserRole.admin))],
            responses=get_resource_by_id_responses)
def get_resource_by_id_endpoint(resource_id: str, db: Session = Depends(get_db)):
    try:
        return get_resource_by_id(db, resource_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))


# Delete Resource
@router.delete("/{resource_id}", 
               response_model = ResourceResponse, 
               status_code = status.HTTP_200_OK, 
               dependencies = [Depends(require_roles(UserRole.professor, UserRole.admin))],
               responses=delete_resource_responses)
def delete_resource_endpoint(resource_id: str, db: Session = Depends(get_db)):
    try:
        return delete_resource(db, resource_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = str(e))
    except FileDeletionError as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = str(e))
    except FolderDeletionError as e:
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail = str(e))