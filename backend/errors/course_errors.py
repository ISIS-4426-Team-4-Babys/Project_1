class CourseNotFoundError(Exception):
    def __init__(self, field: str, value:str):
        self.field = field
        self.value = value
        super().__init__(f"Course not found with {field}={value}")

class DuplicateCourseError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Duplicate course with {field}={value}")

class InvalidUserRoleError(Exception):
    def __init__(self, role: str, expected: str):
        self.role = role
        self.expected = expected
        super().__init__(f"Invalid role {role}. Expected role {expected}")