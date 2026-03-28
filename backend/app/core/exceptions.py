from typing import Optional


class AppError(Exception):
    def __init__(self, message: str, detail: Optional[str] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}: {self.detail}" if self.detail else self.message


class ValidationError(AppError): pass
class NotFoundError(AppError): pass
class AuthError(AppError): pass
class ForbiddenError(AppError): pass
class ConflictError(AppError): pass
class RateLimitError(AppError): pass
class AIServiceError(AppError): pass
class DatabaseError(AppError): pass
class ConfigurationError(AppError): pass
class InterviewStateError(AppError): pass
class InterviewSessionError(AppError): pass
class CVProcessingError(AppError): pass


def get_http_status_code(exception: AppError) -> int:
    status_map = {
        ValidationError: 422,
        NotFoundError: 404,
        AuthError: 401,
        ForbiddenError: 403,
        ConflictError: 409,
        RateLimitError: 429,
        InterviewStateError: 409,
        InterviewSessionError: 400,
        CVProcessingError: 422,
        AIServiceError: 502,
        DatabaseError: 500,
        ConfigurationError: 500,
    }
    return status_map.get(type(exception), 500)


def get_error_code(exception: AppError) -> str:
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', exception.__class__.__name__).lower()
