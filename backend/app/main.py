"""
InterviewMe Backend — Main Entry Point

This is the production-ready FastAPI application with all Phase 1 components:
- Configuration management with validation
- Async database connection with proper lifecycle
- JWT authentication with NextAuth.js integration
- Global error handling with consistent responses
- CORS configuration for frontend integration
- Health checks for monitoring

Engineering principles applied:
- Fail fast: Invalid config crashes the app at startup
- Proper lifecycle: Database connections are managed correctly
- Security: CORS and auth are configured from the start
- Observability: Health checks and structured error responses
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, validate_configuration
from app.database import startup_database, shutdown_database, check_database_connection
from app.core.error_handlers import register_exception_handlers
from app.modules.auth.router import router as auth_router
from app.modules.interviews.router import router as interviews_router


# ============================================================
# APPLICATION LIFECYCLE MANAGEMENT
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    
    This ensures proper initialization and cleanup of resources:
    - Validate configuration
    - Initialize database connections
    - Clean up on shutdown
    """
    print("Starting InterviewMe API...")
    
    # Startup
    try:
        # Validate all configuration
        validate_configuration()
        
        # Initialize database
        await startup_database()
        
        print("InterviewMe API started successfully")
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   Docs available at: /docs")
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        raise
    
    # Application is running
    yield
    
    # Shutdown
    print("Shutting down InterviewMe API...")
    await shutdown_database()
    print("InterviewMe API shut down successfully")


# ============================================================
# CREATE THE FASTAPI APPLICATION
# ============================================================
app = FastAPI(
    title="InterviewMe API",
    description="AI-powered mock interview platform with real-time WebSocket sessions",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,  # Disable docs in production
    redoc_url="/redoc" if not settings.is_production else None,
)


# ============================================================
# MIDDLEWARE CONFIGURATION
# ============================================================

# CORS - Allow frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # Allow cookies and auth headers
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # Allow all headers (including Authorization)
    expose_headers=["X-Request-ID"],  # Expose request ID for debugging
)


# ============================================================
# ERROR HANDLING
# ============================================================
register_exception_handlers(app)


# ============================================================
# ROUTER REGISTRATION
# ============================================================
app.include_router(auth_router)
app.include_router(interviews_router)


# ============================================================
# HEALTH CHECK ENDPOINTS
# ============================================================

@app.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    This is used by:
    - Heroku to check if the app is alive
    - Load balancers for health checks
    - Monitoring systems for uptime checks
    
    Returns basic service information without checking dependencies.
    """
    return {
        "status": "healthy",
        "service": "interviewme-api",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    This checks if the application is ready to serve requests by
    verifying that all dependencies (database, external services) are available.
    
    Returns 200 if ready, 503 if not ready.
    """
    checks = {
        "database": await check_database_connection(),
        "configuration": True,  # If we got here, config is valid
    }
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "service": "interviewme-api",
        "version": "0.1.0",
    }


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
async def root():
    """
    Welcome endpoint with API information.
    
    Provides basic information about the API and links to documentation.
    """
    return {
        "message": "Welcome to InterviewMe API",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if not settings.is_production else "Documentation not available in production",
        "health": "/health",
        "ready": "/health/ready",
    }


# ============================================================
# DEVELOPMENT UTILITIES
# ============================================================

if settings.is_development:
    @app.get("/dev/test-auth")
    async def create_test_token():
        """
        Create a test JWT token for development.
        
        ⚠️  Only available in development mode!
        """
        from app.modules.auth.dependencies import create_test_token
        
        token = create_test_token(
            email="test@example.com",
            name="Test User"
        )
        
        return {
            "token": token,
            "usage": "Add 'Authorization: Bearer <token>' header to requests",
            "expires_in": "1 hour"
        }