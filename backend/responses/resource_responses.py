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

openapi_extra = {
  "requestBody": {
    "content": {
      "multipart/form-data": {
        "schema": {
          "title": "CreateResourceRequest",
          "type": "object",
          "properties": {
            "file": {"type": "string", "format": "binary"},
            "name": {"type": "string"},
            "consumed_by": {"type": "string"},
            "total_docs": {"type": "integer"}
          },
          "required": ["file", "name", "consumed_by", "total_docs"]
        }
      }
    }
  }
}