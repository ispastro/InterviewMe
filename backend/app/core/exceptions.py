"""
InterviewMe Custom Exceptions

This module defines all custom exception classes used throughout the application.
Each exception maps to a specific HTTP status code and provides consistent
error responses to the frontend.

Engineering decisions:
- Inherit from base AppError for common functionality
- Map each exception type to appropriate HTTP status codes
- Include optional detail field for debugging information
- Use descriptive names that indicate the problem domain
"""

from typing import Optional


class AppError(Exception):
    """
    Base exception class for all application-specific errors.
    
    All custom exceptions should inherit from this class to ensure
    consistent error handling and logging.
    """
    
    def __init__(self, message: str, detail: Optional[str] = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.detail:
            return f"{self.message}: {self.detail}"
        return self.message


# ============================================================
# CLIENT ERROR EXCEPTIONS (4xx)
# ============================================================

class ValidationError(AppError):
    """
    Input validation failed.
    Maps to HTTP 422 Unprocessable Entity.
    
    Use when:
    - Pydantic validation fails
    - Business rule validation fails
    - File format is invalid
    """
    pass


class NotFoundError(AppError):
    """
    Requested resource not found.
    Maps to HTTP 404 Not Found.
    
    Use when:
    - Interview ID doesn't exist
    - User not found
    - File not found
    """
    pass


class AuthError(AppError):
    """
    Authentication failed.
    Maps to HTTP 401 Unauthorized.
    
    Use when:
    - JWT token is invalid or expired
    - User not authenticated
    - Token signature verification fails
    """
    pass


class ForbiddenError(AppError):
    """
    User doesn't have permission for this action.
    Maps to HTTP 403 Forbidden.
    
    Use when:
    - User tries to access another user's interview
    - User exceeds rate limits
    - Feature not available for user's plan
    """
    pass


class ConflictError(AppError):
    """
    Request conflicts with current state.
    Maps to HTTP 409 Conflict.
    
    Use when:
    - Interview already in progress
    - User already exists
    - Resource state prevents the operation
    """
    pass


class RateLimitError(AppError):
    """
    Rate limit exceeded.
    Maps to HTTP 429 Too Many Requests.
    
    Use when:
    - User exceeds interview creation limit
    - Too many WebSocket connections
    - API rate limit hit
    """
    pass


# ============================================================
# SERVER ERROR EXCEPTIONS (5xx)
# ============================================================

class AIServiceError(AppError):
    """
    External AI service (Groq) error.
    Maps to HTTP 502 Bad Gateway.
    
    Use when:
    - Groq API is down or returns error
    - AI response parsing fails
    - Timeout waiting for AI response
    """
    pass


class DatabaseError(AppError):
    """
    Database operation failed.
    Maps to HTTP 500 Internal Server Error.
    
    Use when:
    - Database connection lost
    - Transaction rollback required
    - Data integrity constraint violated
    """
    pass


class ConfigurationError(AppError):
    """
    Application configuration error.
    Maps to HTTP 500 Internal Server Error.
    
    Use when:
    - Required environment variable missing
    - Invalid configuration value
    - Service initialization fails
    """
    pass


# ============================================================
# INTERVIEW-SPECIFIC EXCEPTIONS
# ============================================================

class InterviewStateError(AppError):
    """
    Interview is in wrong state for requested operation.
    Maps to HTTP 409 Conflict.
    
    Use when:
    - Trying to start interview that's not READY
    - Trying to get feedback before interview is COMPLETED
    - WebSocket connection to non-IN_PROGRESS interview
    """
    pass


class InterviewSessionError(AppError):
    """
    WebSocket interview session error.
    Maps to HTTP 400 Bad Request.
    
    Use when:
    - Invalid WebSocket message format
    - Session state corruption
    - Unexpected message type for current phase
    """
    pass


class CVProcessingError(AppError):
    """
    CV/JD processing failed.
    Maps to HTTP 422 Unprocessable Entity.
    
    Use when:
    - CV text extraction fails
    - CV content is empty or unreadable
    - AI analysis of CV/JD fails
    """
    pass


# ============================================================
# EXCEPTION UTILITIES
# ============================================================

def get_http_status_code(exception: AppError) -> int:
    """
    Map exception types to HTTP status codes.
    
    This is used by the global exception handler to return
    appropriate HTTP status codes for each exception type.
    """
    status_map = {
        # Client errors (4xx)
        ValidationError: 422,
        NotFoundError: 404,
        AuthError: 401,
        ForbiddenError: 403,
        ConflictError: 409,
        RateLimitError: 429,
        InterviewStateError: 409,
        InterviewSessionError: 400,
        CVProcessingError: 422,
        
        # Server errors (5xx)
        AIServiceError: 502,
        DatabaseError: 500,
        ConfigurationError: 500,
    }
    
    return status_map.get(type(exception), 500)


def get_error_code(exception: AppError) -> str:
    """
    Generate a consistent error code from exception class name.
    
    Examples:
    - ValidationError -> "validation_error"
    - NotFoundError -> "not_found_error"
    - AIServiceError -> "ai_service_error"
    """
    class_name = exception.__class__.__name__
    # Convert CamelCase to snake_case
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()