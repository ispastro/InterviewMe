import traceback
import uuid
from typing import Dict, Any

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError, get_http_status_code, get_error_code
from app.config import settings


def create_error_response(error_code: str, message: str, detail: str = None, request_id: str = None) -> Dict[str, Any]:
    response = {"error": error_code, "message": message}
    if detail and not settings.is_production:
        response["detail"] = detail
    if request_id:
        response["request_id"] = request_id
    return response


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = str(uuid.uuid4())
    status_code = get_http_status_code(exc)
    error_code = get_error_code(exc)
    _log_error(request, exc, request_id, status_code)
    return JSONResponse(
        status_code=status_code,
        content=create_error_response(error_code, exc.message, exc.detail, request_id),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = str(uuid.uuid4())
    errors = [
        {"field": " -> ".join(str(loc) for loc in e["loc"]), "message": e["msg"], "type": e["type"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            "validation_error",
            "Request validation failed",
            {"errors": errors} if not settings.is_production else None,
            request_id,
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = str(uuid.uuid4())
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(f"http_{exc.status_code}", str(exc.detail), request_id=request_id),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid.uuid4())
    print(f"Unhandled Exception [{request_id}]: {type(exc).__name__} — {request.method} {request.url}")
    if settings.is_development:
        print(traceback.format_exc())
    message = str(exc) if settings.is_development else "An unexpected error occurred"
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            "internal_server_error",
            message,
            traceback.format_exc() if settings.is_development else None,
            request_id,
        ),
    )


def _log_error(request: Request, exc: AppError, request_id: str, status_code: int):
    level = "ERROR" if status_code >= 500 else "WARN"
    print(f"{level} [{request_id}]: {type(exc).__name__} — {request.method} {request.url} — {exc.message}")
    if exc.detail:
        print(f"  Detail: {exc.detail}")


def register_exception_handlers(app):
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
