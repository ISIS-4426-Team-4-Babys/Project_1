class ResourceNotFoundError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Resource not found with {field}={value}")

class DuplicateResourceError(Exception):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Resource with name {name} already exists")
