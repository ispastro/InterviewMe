from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MAX_TOKENS: int = 2048
    GROQ_TEMPERATURE: float = 0.7

    # Upstash Redis (caching, sessions, rate limiting)
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""
    REDIS_ENABLED: bool = False
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    ENVIRONMENT: str = "development"
    APP_DEBUG: bool = False

    MAX_INTERVIEWS_PER_USER_PER_DAY: int = 10
    MAX_WEBSOCKET_CONNECTIONS_PER_USER: int = 3

    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "docx", "txt"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def database_echo(self) -> bool:
        return self.is_development and self.APP_DEBUG


settings = Settings()


def validate_configuration():
    """Validate critical configuration on startup."""
    valid_prefixes = (
        "postgresql://", "postgresql+asyncpg://",
        "postgres://",  # Heroku format
        "sqlite+aiosqlite://",
    )
    if not settings.DATABASE_URL.startswith(valid_prefixes):
        raise ValueError(f"DATABASE_URL must start with one of {valid_prefixes}")

    if len(settings.JWT_SECRET) < 32:
        raise ValueError("JWT_SECRET must be at least 32 characters for security")

    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "":
        raise ValueError("GROQ_API_KEY is required for AI functionality")

    for origin in settings.CORS_ORIGINS:
        if not origin.startswith(("http://", "https://")):
            raise ValueError(f"CORS origin must start with http:// or https://. Got: {origin}")

    if settings.is_production:
        if settings.APP_DEBUG:
            raise ValueError("APP_DEBUG must be False in production")
        if "localhost" in str(settings.CORS_ORIGINS):
            print("⚠️  WARNING: localhost in CORS_ORIGINS in production environment")

    print(f"✅ Configuration validated — env: {settings.ENVIRONMENT}, model: {settings.GROQ_MODEL}")
