from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID
import jwt
import secrets
from bcrypt import hashpw, gensalt, checkpw
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config.settings import settings
from app.dependencies.auth import create_access_token, get_token_expiry_seconds
from app.dependencies.referral_code import generate_referral_code
from app.models.user import User
from app.schemas.auth import GoogleCallBack
import requests
from google.oauth2 import id_token
from dotenv import load_dotenv
from cachetools import TTLCache
from app.schemas.user import UserGoogleCreate
import os

load_dotenv()

# Cache for verification codes: TTL 5 minutes (300 seconds)
Verification_cache = TTLCache(maxsize=1000, ttl=300)

EMAIL_VERIFICATION_EXPIRE_HOURS = 24
PASSWORD_RESET_EXPIRE_HOURS = 1

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_verification_token(user_id: str, email: str, purpose: str = "email_verification") -> str:
    """
    Create a token for email verification or password reset.

    Args:
        user_id: User's ID
        email: User's email
        purpose: Token purpose ('email_verification' or 'password_reset')

    Returns:
        JWT token string
    """

    if purpose == "password_reset":
        expire_delta = timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
    else:
        expire_delta = timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)

    expire = datetime.now(timezone.utc) + expire_delta

    payload = {
        "sub": str(user_id),
        "email": email,
        "purpose": purpose,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm=settings.ALGORITHM)


def verify_verification_token(token: str, expected_purpose: str) -> Tuple[str, str]:
    """
    Verify and decode a verification token.

    Args:
        token: JWT token string
        expected_purpose: Expected purpose of the token

    Returns:
        Tuple of (user_id, email)

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_PUBLIC_KEY, algorithms=[settings.ALGORITHM])

        purpose = payload.get("purpose")
        if purpose != expected_purpose:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token purpose"
            )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token payload"
            )

        return user_id, email

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )


def generate_verification_code() -> str:
    """
    Generate a secure 6-digit verification code.

    Returns:
        6-digit string code (100000-999999)
    """
    return str(secrets.randbelow(900000) + 100000)


def store_verification_code(email: str, code: str, user_id: str) -> None:
    """
    Store verification code in cache.

    Args:
        email: User's email (cache key)
        code: 6-digit verification code
        user_id: User's ID
    """
    Verification_cache[email.lower()] = {
        "code": code,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc)
    }


def verify_stored_code(email: str, submitted_code: str) -> str:
    """
    Verify submitted code against stored code.

    Args:
        email: User's email
        submitted_code: Code submitted by user

    Returns:
        User ID if code is valid

    Raises:
        HTTPException: If code is invalid or expired
    """
    email_lower = email.lower()

    if email_lower not in Verification_cache:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new one."
        )

    stored_data = Verification_cache[email_lower]

    if stored_data["code"] != submitted_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    # Remove code from cache after successful verification
    del Verification_cache[email_lower]

    return stored_data["user_id"]


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email address"""
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by ID"""
    statement = select(User).where(User.id == user_id)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def signup_user(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        referred_by: Optional[str] = None
) -> User:
    """
    Create a new user account.

    Args:
        db: Database session
        username: User's username
        email: User's email
        password: Plain text password
        referred_by: Optional referral code

    Returns:
        Created User object

    Raises:
        HTTPException: If user already exists
    """
    referral_code = await generate_referral_code(username)

    hashed_password = hash_password(password)

    # Create user object
    user = User(
        username=username,
        email=email,
        password=hashed_password,
        referred_by=referred_by or "",
        referral_code=referral_code,
        email_verified=False
    )

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()

        if "email" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists"
            )
        elif "username" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )


async def login_user(db: AsyncSession, email: str, password: str) -> Tuple[User, str, int]:
    """
    Authenticate user and generate access token.

    Args:
        db: Database session
        email: User's email
        password: Plain text password

    Returns:
        Tuple of (User, access_token, expires_in_seconds)

    Raises:
        HTTPException: If credentials are invalid
    """
    user = await get_user_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email
    )

    return user, access_token, get_token_expiry_seconds()


async def verify_user_email(db: AsyncSession, token: str) -> User:
    """
    Verify user's email using verification token.

    Args:
        db: Database session
        token: Verification token

    Returns:
        Updated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    user_id_str, email = verify_verification_token(token, "email_verification")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID in token"
        )

    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.email != email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email mismatch"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )

    user.email_verified = True
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def verify_user_email_with_code(db: AsyncSession, email: str, code: str) -> User:
    """
    Verify user's email using 6-digit verification code.

    Args:
        db: Database session
        email: User's email address
        code: 6-digit verification code

    Returns:
        Updated User object

    Raises:
        HTTPException: If code is invalid, expired, or user not found
    """
    # Verify the code and get user_id
    user_id_str = verify_stored_code(email, code)

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.email.lower() != email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email mismatch"
        )

    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )

    user.email_verified = True
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def reset_user_password(db: AsyncSession, token: str, new_password: str) -> User:
    """
    Reset user's password using reset token.

    Args:
        db: Database session
        token: Password reset token
        new_password: New plain text password

    Returns:
        Updated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    user_id_str, email = verify_verification_token(token, "password_reset")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID in token"
        )

    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.email != email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email mismatch"
        )

    user.password = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


def generate_verification_link(token: str, base_url: str = "https://confess.com.ng") -> str:
    """Generate email verification link"""
    return f"{base_url}/verify-email?token={token}"


def generate_password_reset_link(token: str, base_url: str = "https://confess.com.ng") -> str:
    """Generate password reset link"""
    return f"{base_url}/reset-password?token={token}"


async def google_callback_login(token: GoogleCallBack, db: AsyncSession) -> Tuple[User, str, int]:
    """

    :param token:
    :param db:
    """

    user_info = id_token.verify_oauth2_token(token.id_token, requests.Request(), GOOGLE_CLIENT_ID)
    user_email = user_info["email"]

    user = await get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email
    )

    return user, access_token, get_token_expiry_seconds()

async def google_callback_signup(token: GoogleCallBack, db: AsyncSession) -> Tuple[User, str, int]:
    """
    Create a new user account via Google OAuth and return access token.

    Args:
        token: Google OAuth callback token containing id_token
        db: Database session

    Returns:
        Tuple of (User, access_token, expires_in_seconds)

    Raises:
        HTTPException: If user already exists or token is invalid
    """
    try:
        # Verify the Google ID token
        user_info = id_token.verify_oauth2_token(token.id_token, requests.Request(), GOOGLE_CLIENT_ID)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {str(e)}"
        )

    user_email = user_info.get("email")
    given_name = user_info.get("given_name", "User")

    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by Google"
        )

    # Check if user already exists
    existing_user = await get_user_by_email(db=db, email=user_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

    # Generate referral code
    referral_code = await generate_referral_code(given_name)

    # Create new user with Google auth
    # For Google auth users, password is not used, so we set it to empty hash
    new_user = User(
        email=user_email,
        username=given_name,
        password=hash_password(""),  # Empty password for Google auth users
        referral_code=referral_code,
        referred_by="",
        google_auth=True,
        email_verified=True,  # Google emails are pre-verified
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()

        if "email" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists"
            )
        elif "username" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )

    # Generate access token
    access_token = create_access_token(
        user_id=str(new_user.id),
        email=new_user.email
    )

    return new_user, access_token, get_token_expiry_seconds()
