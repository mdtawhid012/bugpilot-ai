
class ApplicationError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(ApplicationError):
    def __init__(self, code: str = "not_found", message: str = "Resource not found") -> None:
        super().__init__(code, message, 404)


class ConflictError(ApplicationError):
    def __init__(self, code: str = "invalid_state", message: str = "The requested operation conflicts with current state") -> None:
        super().__init__(code, message, 409)


class CapacityExhaustedError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("coordinator_capacity_exhausted", "The investigation coordinator has no available capacity", 503)