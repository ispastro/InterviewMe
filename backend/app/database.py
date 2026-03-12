"""
InterviewMe Database Layer

This module sets up async SQLAlchemy 2.0 with proper connection pooling,
session management, and a base model with common fields.

Engineering decisions:
- Async engine for non-blocking database operations
- Connection pooling with health checks (pool_pre_ping)
- Session-per-request pattern via FastAPI dependency
- UUID primary keys for better distributed system support
- Automatic created_at/updated_at timestamps
- Proper error handling and cleanup
"""

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings


# ============================================================
# DATABASE ENGINE SETUP
# ============================================================
# The engine manages the connection pool to PostgreSQL.
# It's created once at module import and reused throughout the app.

# Check if we're using SQLite (for testing) or PostgreSQL (for production)
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite configuration - no connection pooling
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.database_echo,     # Log SQL queries in development
        future=True,                     # Use SQLAlchemy 2.0 style
    )
else:
    # PostgreSQL configuration - with connection pooling
    engine = create_async_engine(
        settings.DATABASE_URL,
        
        # Connection pool settings
        pool_size=10,                    # Number of connections to maintain
        max_overflow=20,                 # Additional connections when pool is full
        pool_pre_ping=True,              # Validate connections before use
        pool_recycle=3600,               # Recycle connections after 1 hour
        
        # Logging
        echo=settings.database_echo,     # Log SQL queries in development
        
        # Performance
        future=True,                     # Use SQLAlchemy 2.0 style
    )


# ============================================================
# SESSION FACTORY
# ============================================================
# Creates new database sessions for each request.
# Sessions are NOT thread-safe, so each request gets its own.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,          # Keep objects usable after commit
    autoflush=True,                  # Auto-flush before queries
    autocommit=False,                # Manual transaction control
)


# ============================================================
# BASE MODEL
# ============================================================
class Base(DeclarativeBase):
    """
    Base class for all database models.
    
    Provides common fields that every table should have:
    - id: UUID primary key (better than auto-increment for distributed systems)
    - created_at: When the record was created
    - updated_at: When the record was last modified
    """
    
    # UUID primary key - generated server-side
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for this record"
    )
    
    # Audit timestamps - automatically managed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When this record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When this record was last updated"
    )
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<{self.__class__.__name__}(id={self.id})>"


# ============================================================
# DATABASE SESSION DEPENDENCY
# ============================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    
    This implements the session-per-request pattern:
    1. Create a new session for each request
    2. Yield it to the endpoint function
    3. Commit the transaction if successful
    4. Rollback if there's an exception
    5. Always close the session
    
    Usage in endpoints:
        async def create_user(db: AsyncSession = Depends(get_db)):
            # Use db here
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # If we get here, no exception occurred
            await session.commit()
        except Exception:
            # Something went wrong, rollback the transaction
            await session.rollback()
            raise  # Re-raise the exception
        finally:
            # Always close the session
            await session.close()


# ============================================================
# DATABASE UTILITIES
# ============================================================
async def create_tables():
    """
    Create all database tables.
    Used during development and testing.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully")


async def drop_tables():
    """
    Drop all database tables.
    ⚠️  DANGEROUS - Only use in development/testing!
    """
    if settings.is_production:
        raise RuntimeError("Cannot drop tables in production!")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Database tables dropped")


async def check_database_connection():
    """
    Test database connectivity.
    Used in health checks and startup validation.
    """
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            # Simple query to test connection
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


# ============================================================
# STARTUP/SHUTDOWN HANDLERS
# ============================================================
async def startup_database():
    """
    Initialize database connection on app startup.
    """
    print("Connecting to database...")
    
    # Test connection
    if not await check_database_connection():
        raise RuntimeError("Failed to connect to database")
    
    print("Database connected: {}".format(settings.DATABASE_URL.split('@')[0] + "@***"))


async def shutdown_database():
    """
    Clean up database connections on app shutdown.
    """
    print("Closing database connections...")
    await engine.dispose()
    print("Database connections closed")