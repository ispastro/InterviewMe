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

security = HTTPBearer(scheme_name="JWT", auto_error=False)


def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": True, "verify_exp": True, "verify_iat": True, "verify_aud": False, "verify_iss": False},
        )
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", "Please log in again")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token", "Token signature verification failed")
    except JWTError as e:
        raise AuthError("Token validation failed", str(e))


def extract_user_info_from_jwt(payload: dict) -> tuple:
    email = payload.get("email")
    if not email:
        raise AuthError("Invalid token", "Email claim missing from token")
    name = payload.get("name")
    oauth_subject = payload.get("sub")
    oauth_provider = None
    if "accounts" in payload:
        accounts = payload["accounts"]
        if accounts:
            oauth_provider = accounts[0].get("provider")
    return email, name, oauth_provider, oauth_subject


async def get_or_create_user(db: AsyncSession, email: str, name: Optional[str] = None, oauth_provider: Optional[str] = None, oauth_subject: Optional[str] = None) -> User:
    try:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.update_from_jwt(name=name)
            await db.flush()
            return user
        user = User.create_from_jwt(email=email, name=name, oauth_provider=oauth_provider, oauth_subject=oauth_subject)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    except Exception as e:
        raise DatabaseError("Failed to get or create user", str(e))


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    try:
        payload = decode_jwt_token(credentials.credentials)
        email, name, oauth_provider, oauth_subject = extract_user_info_from_jwt(payload)
        return await get_or_create_user(db, email, name, oauth_provider, oauth_subject)
    except AuthError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_jwt_token(credentials.credentials)
        email, name, oauth_provider, oauth_subject = extract_user_info_from_jwt(payload)
        return await get_or_create_user(db, email, name, oauth_provider, oauth_subject)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message, headers={"WWW-Authenticate": "Bearer"})
    except DatabaseError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication service unavailable")


async def get_current_user_websocket(token: str, db: AsyncSession) -> Optional[User]:
    if not token:
        return None
    try:
        payload = decode_jwt_token(token)
        email, name, oauth_provider, oauth_subject = extract_user_info_from_jwt(payload)
        return await get_or_create_user(db, email, name, oauth_provider, oauth_subject)
    except (AuthError, DatabaseError):
        return None


def create_test_token(email: str, name: str = None) -> str:
    if settings.is_production:
        raise RuntimeError("Cannot create test tokens in production!")
    import time
    payload = {"email": email, "name": name, "sub": f"test-{email}", "iat": int(time.time()), "exp": int(time.time()) + 3600}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
