"""
InterviewMe Backend Configuration

This is the single source of truth for all application settings.
Pydantic validates all environment variables at startup - if any required
variable is missing or has wrong type, the app won't start (fail fast).

Engineering decisions:
- Use Pydantic for type validation and IDE support
- Default values for non-sensitive settings
- List parsing for CORS_ORIGINS
- Environment-aware configuration
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All sensitive values (API keys, secrets) must be provided via env vars.
    Non-sensitive values have sensible defaults.
    """
    
    # ============================================================
    # DATABASE CONFIGURATION
    # ============================================================
    DATABASE_URL: str  # Required - no default for critical infrastructure
    
    # ============================================================
    # AUTHENTICATION
    # ============================================================
    # These MUST match your NextAuth.js configuration exactly
    JWT_SECRET: str                    # Required - shared secret with frontend
    JWT_ALGORITHM: str = "HS256"       # Standard HMAC SHA-256
    
    # ============================================================
    # GROQ AI CONFIGURATION  
    # ============================================================
    GROQ_API_KEY: str                  # Required - get from console.groq.com
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Fast, high-quality model
    GROQ_MAX_TOKENS: int = 2048        # Response limit per call
    GROQ_TEMPERATURE: float = 0.7      # Creativity vs consistency balance
    
    # ============================================================
    # APPLICATION SETTINGS
    # ============================================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]  # Frontend URLs
    ENVIRONMENT: str = "development"    # development, staging, production
    APP_DEBUG: bool = False             # Enable debug logging (renamed to avoid conflicts)
    
    # ============================================================
    # RATE LIMITING
    # ============================================================
    MAX_INTERVIEWS_PER_USER_PER_DAY: int = 10
    MAX_WEBSOCKET_CONNECTIONS_PER_USER: int = 3
    
    # ============================================================
    # FILE UPLOAD LIMITS
    # ============================================================
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "docx", "txt"]
    
    # ============================================================
    # PYDANTIC CONFIGURATION
    # ============================================================
    model_config = SettingsConfigDict(
        env_file=".env",               # Load from .env file if present
        env_file_encoding="utf-8",     # Handle unicode in env files
        case_sensitive=False,          # Allow lowercase env var names
        extra="ignore"                 # Ignore unknown env vars
    )
    
    # ============================================================
    # COMPUTED PROPERTIES
    # ============================================================
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def database_echo(self) -> bool:
        """Should SQLAlchemy log all SQL queries?"""
        return self.is_development and self.APP_DEBUG


# ============================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================
# This is created once at module import time.
# If any required env var is missing, the app will crash here
# with a clear error message (fail fast principle).
settings = Settings()


# ============================================================
# CONFIGURATION VALIDATION
# ============================================================
def validate_configuration():
    """
    Additional validation that can't be done in Pydantic.
    Call this during app startup.
    """
    # Validate database URL format
    valid_prefixes = (
        "postgresql://", "postgresql+asyncpg://",  # PostgreSQL
        "sqlite+aiosqlite://"  # SQLite for testing
    )
    if not settings.DATABASE_URL.startswith(valid_prefixes):
        raise ValueError(
            f"DATABASE_URL must start with one of {valid_prefixes}. "
            f"Got: {settings.DATABASE_URL[:20]}..."
        )
    
    # Validate JWT secret strength
    if len(settings.JWT_SECRET) < 32:
        raise ValueError("JWT_SECRET must be at least 32 characters long for security")
    
    # Validate CORS origins format
    for origin in settings.CORS_ORIGINS:
        if not origin.startswith(("http://", "https://")):
            raise ValueError(f"CORS origin must start with http:// or https://. Got: {origin}")
    
    print(f"Configuration validated successfully")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Database: {settings.DATABASE_URL.split('@')[0]}@***")  # Hide credentials
    print(f"   CORS Origins: {settings.CORS_ORIGINS}")
    print(f"   Groq Model: {settings.GROQ_MODEL}")