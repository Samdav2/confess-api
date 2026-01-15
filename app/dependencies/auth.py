"""
JWT Authentication Dependencies with RSA (RS256)

This module provides JWT token generation and validation using RSA public/private key pairs.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config.settings import settings
from app.db.sessions import get_session
from app.models.user import User
from app.schemas.auth import TokenData
from sqlmodel import select


# OAuth2 scheme for Bearer token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def create_access_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token using RSA private key.

    Args:
        user_id: The user's unique identifier
        email: The user's email address
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Raises:
        HTTPException: If private key is not configured
    """
    if not settings.JWT_PRIVATE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT private key not configured"
        )

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_PRIVATE_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token using RSA public key.

    Args:
        token: The JWT token string to verify

    Returns:
        TokenData containing the decoded payload

    Raises:
        HTTPException: If token is invalid, expired, or public key not configured
    """
    if not settings.JWT_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT public key not configured"
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        exp: datetime = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)

        if user_id is None:
            raise credentials_exception

        return TokenData(user_id=user_id, email=email, exp=exp)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header (injected by oauth2_scheme)
        db: Database session (injected)

    Returns:
        The authenticated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token_data = verify_token(token)

    try:
        user_id = UUID(token_data.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query user from database
    statement = select(User).where(User.id == user_id)
    result = await db.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active (email verified) user.

    Args:
        current_user: The authenticated user (injected)

    Returns:
        The authenticated and verified User object

    Raises:
        HTTPException: If user's email is not verified
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    return current_user


def get_token_expiry_seconds() -> int:
    """Get token expiry time in seconds for API responses"""
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
