class ResourceNotFoundError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Resource not found with {field}={value}")

class DuplicateResourceError(Exception):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Resource with name {name} already exists")

class InvalidFileTypeError(Exception):
    def __init__(self, filetype: str):
        self.filetype = filetype
        super().__init__(f"Invalid file type: {filetype}. Allowed types are: pdf, docx, pptx, txt, md")

class FileSizeError(Exception):
    def __init__(self, size: int, max_size: int):
        self.size = size
        self.max_size = max_size
        super().__init__(f"File size {size} bytes exceeds maximum allowed size of {max_size} bytes")
