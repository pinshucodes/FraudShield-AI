class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message  
        self.status_code = status_code

class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__("NOT_FOUND", message, 404)

class UnauthorizedError(AppException):
    def __init__(self, code: str = "UNAUTHORIZED", message: str = "Not authorized"):
        super().__init__(code, message, 401)

class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__("FORBIDDEN", message, 403)

class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict"):
        super().__init__("CONFLICT", message, 409)

class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__("VALIDATION_ERROR", message, 422)

class RateLimitError(AppException):
    def __init__(self, message: str = "Too many requests"):
        super().__init__("RATE_LIMIT", message, 429)
