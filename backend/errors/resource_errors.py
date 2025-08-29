class ResourceNotFoundError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Resource not found with {field}={value}")

class DuplicateResourceError(Exception):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Resource with name {name} already consumed by the agent")

class FileSizeError(Exception):
    def __init__(self, size: int, max_size: int):
        self.size = size
        self.max_size = max_size
        super().__init__(f"File size {size} bytes exceeds maximum allowed size of {max_size} bytes")

class FileDeletionError(Exception):
    def __init__(self, path: str, error: str):
        self.path = path
        self.error = error
        super().__init__(f"Failed to delete file at {path}: {error}")

class FolderDeletionError(Exception):
    def __init__(self, path: str, error: str):
        self.path = path
        self.error = error
        super().__init__(f"Failed to delete folder at {path}: {error}")