"""
InterviewMe Global Error Handlers

This module provides centralized error handling for the FastAPI application.
All exceptions are converted to consistent JSON responses with appropriate
HTTP status codes and structured error information.

Engineering decisions:
- Consistent error response format across all endpoints
- Proper HTTP status code mapping
- Detailed logging for debugging
- Security-conscious error messages (no sensitive data leakage)
- Request ID tracking for error correlation
"""

import traceback
import uuid
from typing import Dict, Any

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError, get_http_status_code, get_error_code
from app.config import settings


# ============================================================
# ERROR RESPONSE FORMAT
# ============================================================

def create_error_response(
    error_code: str,
    message: str,
    detail: str = None,
    request_id: str = None
) -> Dict[str, Any]:
    """
    Create a standardized error response format.
    
    This ensures all API errors return the same JSON structure,
    making it easier for the frontend to handle errors consistently.
    """
    response = {
        "error": error_code,
        "message": message,
        "timestamp": "2024-01-01T00:00:00Z",  # Will be set by middleware
    }
    
    if detail and not settings.is_production:
        # Only include detailed error info in development
        response["detail"] = detail
    
    if request_id:
        response["request_id"] = request_id
    
    return response


# ============================================================
# CUSTOM EXCEPTION HANDLERS
# ============================================================

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Handle all custom application exceptions.
    
    This is the main error handler that converts our custom exceptions
    into properly formatted JSON responses with correct HTTP status codes.
    """
    # Generate request ID for error tracking
    request_id = str(uuid.uuid4())
    
    # Get HTTP status code for this exception type
    status_code = get_http_status_code(exc)
    error_code = get_error_code(exc)
    
    # Log the error for debugging
    log_error(request, exc, request_id, status_code)
    
    # Create response
    response_data = create_error_response(
        error_code=error_code,
        message=exc.message,
        detail=exc.detail,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    These occur when request data doesn't match the expected schema
    (wrong types, missing required fields, etc.).
    """
    request_id = str(uuid.uuid4())
    
    # Extract validation error details
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    # Log validation error
    print(f"Validation Error [{request_id}]: {request.method} {request.url}")
    print(f"   Errors: {errors}")
    
    response_data = create_error_response(
        error_code="validation_error",
        message="Request validation failed",
        detail={"errors": errors} if not settings.is_production else None,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=422,
        content=response_data
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle standard FastAPI HTTP exceptions.
    
    This catches HTTPException instances that might be raised directly
    by FastAPI or third-party libraries.
    """
    request_id = str(uuid.uuid4())
    
    # Log HTTP exception
    print(f"HTTP Exception [{request_id}]: {exc.status_code} - {exc.detail}")
    print(f"   Request: {request.method} {request.url}")
    
    response_data = create_error_response(
        error_code=f"http_{exc.status_code}",
        message=str(exc.detail),
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions that aren't caught by other handlers.
    
    This is the last resort handler for bugs and unexpected errors.
    In production, it returns a generic error message to avoid
    leaking sensitive information.
    """
    request_id = str(uuid.uuid4())
    
    # Log the full exception with traceback
    print(f"Unhandled Exception [{request_id}]: {type(exc).__name__}")
    print(f"   Request: {request.method} {request.url}")
    print(f"   Error: {str(exc)}")
    
    if settings.is_development:
        # Include full traceback in development
        print(f"   Traceback:\n{traceback.format_exc()}")
    
    # Generic error message for production
    message = str(exc) if settings.is_development else "An unexpected error occurred"
    
    response_data = create_error_response(
        error_code="internal_server_error",
        message=message,
        detail=traceback.format_exc() if settings.is_development else None,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content=response_data
    )


# ============================================================
# ERROR LOGGING
# ============================================================

def log_error(request: Request, exc: AppError, request_id: str, status_code: int):
    """
    Log error details for debugging and monitoring.
    
    In production, you'd send this to a logging service like
    CloudWatch, Datadog, or Sentry.
    """
    # Determine log level based on status code
    if status_code >= 500:
        level = "ERROR"
        emoji = "ERROR"
    elif status_code >= 400:
        level = "WARN"
        emoji = "WARN"
    else:
        level = "INFO"
        emoji = "INFO"
    
    # Log structured error information
    print(f"{emoji} {level} [{request_id}]: {type(exc).__name__}")
    print(f"   Request: {request.method} {request.url}")
    print(f"   Message: {exc.message}")
    
    if exc.detail:
        print(f"   Detail: {exc.detail}")
    
    # Log user context if available
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        print(f"   User: {user_id}")
    
    # In production, send to monitoring service
    if settings.is_production:
        # TODO: Send to Sentry, CloudWatch, etc.
        pass


# ============================================================
# EXCEPTION HANDLER REGISTRATION
# ============================================================

def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.
    
    Call this from main.py during app initialization.
    """
    # Custom application exceptions
    app.add_exception_handler(AppError, app_error_handler)
    
    # Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    
    # Standard HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, generic_exception_handler)
    
    print("Exception handlers registered")