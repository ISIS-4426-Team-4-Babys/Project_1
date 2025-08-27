class IntegrityConstraintError(Exception):
    def __init__(self, entity: str):
        self.entity = entity
        super().__init__(f"Integrity constraint violated: {entity}")
