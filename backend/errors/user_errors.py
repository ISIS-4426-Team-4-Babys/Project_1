class UserNotFoundError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"User not found with {field}={value}")

class DuplicateUserError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Duplicate user with {field}={value}")

class InvalidCredentialsError(Exception):
    def __init__(self):
        super().__init__("Invalid email or password")
