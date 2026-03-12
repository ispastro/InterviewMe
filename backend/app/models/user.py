"""
InterviewMe User Model

This model represents users in our system. Users are created automatically
when they first authenticate via NextAuth.js (Google OAuth or email).

Engineering decisions:
- UUID primary key for better distributed system support
- Email as unique identifier (required for OAuth)
- Nullable name field (some OAuth providers don't provide names)
- OAuth provider tracking for analytics and debugging
- Soft relationship to interviews (no foreign key constraints for flexibility)
"""

from typing import Optional, List
from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """
    User model for authentication and profile management.
    
    Users are automatically created when they first authenticate
    via NextAuth.js. The backend never handles passwords or OAuth flows
    directly - it only validates JWTs and manages user profiles.
    """
    
    __tablename__ = "users"
    
    # ============================================================
    # CORE FIELDS
    # ============================================================
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,  # Fast lookups during auth
        comment="User's email address from OAuth provider"
    )
    
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="User's display name (may be null for some OAuth providers)"
    )
    
    # ============================================================
    # OAUTH INTEGRATION
    # ============================================================
    
    oauth_provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="OAuth provider: 'google', 'github', etc. Null for email auth"
    )
    
    oauth_subject: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="OAuth provider's user ID (sub claim from JWT)"
    )
    
    # ============================================================
    # USER PREFERENCES
    # ============================================================
    
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Whether the user account is active"
    )
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    # Note: We use back_populates instead of backref for explicit control
    
    # One user can have many interviews
    interviews: Mapped[List["Interview"]] = relationship(
        "Interview",
        back_populates="user",
        cascade="all, delete-orphan",  # Delete interviews when user is deleted
        lazy="select",  # Load interviews only when accessed
        order_by="Interview.created_at.desc()"  # Most recent first
    )
    
    # ============================================================
    # INDEXES FOR PERFORMANCE
    # ============================================================
    
    __table_args__ = (
        # Composite index for OAuth lookups
        Index("idx_user_oauth", "oauth_provider", "oauth_subject"),
        
        # Index for active user queries
        Index("idx_user_active", "is_active"),
    )
    
    # ============================================================
    # METHODS
    # ============================================================
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<User(id={self.id}, email={self.email}, provider={self.oauth_provider})>"
    
    @property
    def display_name(self) -> str:
        """
        Get the best available display name for the user.
        Falls back to email if name is not available.
        """
        return self.name or self.email.split("@")[0]
    
    @property
    def is_oauth_user(self) -> bool:
        """Check if user authenticated via OAuth (vs email/password)"""
        return self.oauth_provider is not None
    
    def to_dict(self) -> dict:
        """
        Convert user to dictionary for API responses.
        
        Note: We don't include oauth_subject for security reasons.
        """
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "display_name": self.display_name,
            "oauth_provider": self.oauth_provider,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    # ============================================================
    # CLASS METHODS FOR USER MANAGEMENT
    # ============================================================
    
    @classmethod
    def create_from_jwt(cls, email: str, name: str = None, oauth_provider: str = None, oauth_subject: str = None) -> "User":
        """
        Create a new user from JWT claims.
        
        This is used during the authentication process when a user
        logs in for the first time.
        
        Args:
            email: User's email from JWT
            name: User's name from JWT (optional)
            oauth_provider: OAuth provider name (google, github, etc.)
            oauth_subject: OAuth provider's user ID
        
        Returns:
            New User instance (not yet saved to database)
        """
        return cls(
            email=email,
            name=name,
            oauth_provider=oauth_provider,
            oauth_subject=oauth_subject,
            is_active=True
        )
    
    def update_from_jwt(self, name: str = None) -> None:
        """
        Update user information from JWT claims.
        
        This is called on each login to keep user info fresh
        (in case they changed their name on the OAuth provider).
        
        Args:
            name: Updated name from JWT
        """
        if name and name != self.name:
            self.name = name
            # updated_at will be set automatically by SQLAlchemy