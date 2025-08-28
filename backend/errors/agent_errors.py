class AgentNotFoundError(Exception):
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Agent not found with {field}={value}")
        