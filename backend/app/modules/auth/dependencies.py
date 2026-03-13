"""
InterviewMe Authentication Dependencies

This module provides FastAPI dependencies for JWT validation and user authentication.
The backend doesn't handle login/signup - it only validates JWTs issued by NextAuth.js.

Engineering decisions:
- Stateless JWT validation (no sessions)
- Automatic user creation on first login (upsert pattern)
- Shared JWT secret with NextAuth.js frontend
- Proper error handling for invalid/expired tokens
- User object caching during request lifecycle
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.core.exceptions import AuthError, DatabaseError


# ============================================================
# JWT SECURITY SCHEME
# ============================================================
# This tells FastAPI to expect "Authorization: Bearer <token>" headers
security = HTTPBearer(
    scheme_name="JWT",
    description="JWT token from NextAuth.js",
    auto_error=False  # We'll handle errors manually for better control
)


# ============================================================
# JWT VALIDATION
# ============================================================

def decode_jwt_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded JWT payload
        
    Raises:
        AuthError: If token is invalid, expired, or malformed
    """
    try:
        # Decode JWT using shared secret with NextAuth.js
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,  # Check expiration
                "verify_iat": True,  # Check issued at
                "verify_aud": False,  # We don't use audience
                "verify_iss": False,  # We don't use issuer
            }
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", "Please log in again")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token", "Token signature verification failed")
    except JWTError as e:
        raise AuthError("Token validation failed", str(e))


def extract_user_info_from_jwt(payload: dict) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
    """
    Extract user information from JWT payload.
    
    Args:
        payload: Decoded JWT payload
        
    Returns:
        Tuple of (email, name, oauth_provider, oauth_subject)
        
    Raises:
        AuthError: If required fields are missing
    """
    # Email is required
    email = payload.get("email")
    if not email:
        raise AuthError("Invalid token", "Email claim missing from token")
    
    # Optional fields
    name = payload.get("name")
    
    # NextAuth.js specific fields
    oauth_provider = None
    oauth_subject = payload.get("sub")  # Subject claim
    
    # Detect OAuth provider from token
    if "accounts" in payload:
        # NextAuth.js includes account info in some tokens
        accounts = payload["accounts"]
        if accounts and len(accounts) > 0:
            oauth_provider = accounts[0].get("provider")
    
    return email, name, oauth_provider, oauth_subject


# ============================================================
# USER MANAGEMENT
# ============================================================

async def get_or_create_user(
    db: AsyncSession,
    email: str,
    name: Optional[str] = None,
    oauth_provider: Optional[str] = None,
    oauth_subject: Optional[str] = None
) -> User:
    """
    Get existing user or create new one (upsert pattern).
    
    This implements the "auto-registration" flow where users are
    created automatically on their first API call after OAuth login.
    
    Args:
        db: Database session
        email: User's email
        name: User's name (optional)
        oauth_provider: OAuth provider name
        oauth_subject: OAuth provider's user ID
        
    Returns:
        User object (existing or newly created)
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Try to find existing user by email
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            # User exists - update their info in case it changed
            user.update_from_jwt(name=name)
            await db.flush()  # Ensure changes are persisted
            return user
        
        # User doesn't exist - create new one
        user = User.create_from_jwt(
            email=email,
            name=name,
            oauth_provider=oauth_provider,
            oauth_subject=oauth_subject
        )
        
        db.add(user)
        await db.flush()  # Get the ID without committing
        await db.refresh(user)  # Load the full object
        
        return user
        
    except Exception as e:
        raise DatabaseError("Failed to get or create user", str(e))


# ============================================================
# FASTAPI DEPENDENCIES
# ============================================================

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT token (optional).
    
    This dependency returns None if no token is provided or if the token
    is invalid. Use this for endpoints that work for both authenticated
    and anonymous users.
    
    Args:
        credentials: JWT credentials from Authorization header
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        # Decode JWT token
        payload = decode_jwt_token(credentials.credentials)
        
        # Extract user info
        email, name, oauth_provider, oauth_subject = extract_user_info_from_jwt(payload)
        
        # Get or create user
        user = await get_or_create_user(
            db=db,
            email=email,
            name=name,
            oauth_provider=oauth_provider,
            oauth_subject=oauth_subject
        )
        
        return user
        
    except AuthError:
        # Invalid token - return None for optional auth
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user from JWT token (required).
    
    This dependency raises an HTTP 401 error if no token is provided
    or if the token is invalid. Use this for protected endpoints.
    
    Args:
        credentials: JWT credentials from Authorization header
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode JWT token
        payload = decode_jwt_token(credentials.credentials)
        
        # Extract user info
        email, name, oauth_provider, oauth_subject = extract_user_info_from_jwt(payload)
        
        # Get or create user
        user = await get_or_create_user(
            db=db,
            email=email,
            name=name,
            oauth_provider=oauth_provider,
            oauth_subject=oauth_subject
        )
        
        return user
        
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


# ============================================================
# WEBSOCKET AUTHENTICATION
# ============================================================

async def get_current_user_websocket(
    token: str,
    db: AsyncSession
) -> Optional[User]:
    """
    Get current user from JWT token for WebSocket connections.
    
    WebSocket connections can't use the standard HTTPBearer dependency,
    so we need a separate function that takes the token as a string parameter.
    
    Args:
        token: JWT token string from query parameter
        db: Database session
        
    Returns:
        User object if authenticated, None if invalid token
    """
    if not token:
        return None
    
    try:
        # Decode JWT token
        payload = decode_jwt_token(token)
        
        # Extract user info
        email, name, oauth_provider, oauth_subject = extract_user_info_from_jwt(payload)
        
        # Get or create user
        user = await get_or_create_user(
            db=db,
            email=email,
            name=name,
            oauth_provider=oauth_provider,
            oauth_subject=oauth_subject
        )
        
        return user
        
    except (AuthError, DatabaseError):
        # Invalid token or database error - return None for WebSocket
        return None


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def create_test_token(email: str, name: str = None) -> str:
    """
    Create a test JWT token for development/testing.
    
    ⚠️  Only use this in development/testing environments!
    
    Args:
        email: User's email
        name: User's name
        
    Returns:
        JWT token string
    """
    if settings.is_production:
        raise RuntimeError("Cannot create test tokens in production!")
    
    import time
    
    payload = {
        "email": email,
        "name": name,
        "sub": f"test-{email}",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1 hour expiry
    }
    
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)