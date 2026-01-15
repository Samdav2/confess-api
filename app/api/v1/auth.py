"""
Authentication API Router

Endpoints for user authentication: login, forgot password, email verification.
"""

from fastapi import APIRouter, Depends, BackgroundTasks, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.sessions import get_session
from app.dependencies.auth import get_current_user
from app.dependencies.email_service import email_service
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SendVerificationRequest,
    SendVerificationResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    UserResponse,
    GoogleCallBack,
)
from app.service.auth import (
    login_user,
    verify_user_email,
    reset_user_password,
    get_user_by_email,
    create_verification_token,
    generate_verification_link,
    generate_password_reset_link,
    google_callback_login,
    google_callback_signup,
)

router = APIRouter()


# ============================================
# Login Endpoints
# ============================================

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login with email and password"
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Authenticate user and return JWT access token.

    - Validates email and password
    - Returns JWT token for authenticated requests
    """
    user, access_token, expires_in = await login_user(
        db=db,
        email=request.email,
        password=request.password
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/token",
    response_model=LoginResponse,
    summary="OAuth2 compatible token endpoint"
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
):
    """
    OAuth2 compatible login endpoint.

    Accepts form data with username (email) and password.
    """
    user, access_token, expires_in = await login_user(
        db=db,
        email=form_data.username,  # OAuth2 uses 'username' field for email
        password=form_data.password
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


# ============================================
# Email Verification Endpoints
# ============================================

@router.post(
    "/send-verification",
    response_model=SendVerificationResponse,
    summary="Send email verification"
)
async def send_verification_email(
    request: SendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Send email verification link to user.

    - Finds user by email
    - Generates new verification token
    - Sends verification email
    """
    user = await get_user_by_email(db, request.email)

    if not user:
        # Don't reveal if email exists for security
        return SendVerificationResponse(
            message="If this email is registered, a verification link has been sent."
        )

    if user.email_verified:
        return SendVerificationResponse(
            message="Email is already verified."
        )

    # Generate verification token and link
    verification_token = create_verification_token(
        user_id=str(user.id),
        email=user.email,
        purpose="email_verification"
    )
    verification_link = generate_verification_link(verification_token)

    # Send verification email
    email_service.send_email_verification(
        background_tasks=background_tasks,
        email_to=user.email,
        name=user.username,
        verification_link=verification_link
    )

    return SendVerificationResponse(
        message="If this email is registered, a verification link has been sent."
    )


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verify email with token"
)
async def verify_email(
    request: VerifyEmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Verify user's email address using verification token.

    - Validates the verification token
    - Marks email as verified
    - Sends confirmation email
    """
    user = await verify_user_email(db, request.token)

    # Send verification success email
    email_service.send_email_verified_notice(
        background_tasks=background_tasks,
        email_to=user.email,
        name=user.username
    )

    return VerifyEmailResponse(
        message="Email verified successfully!",
        email_verified=True
    )


@router.get(
    "/resend-verification",
    response_model=SendVerificationResponse,
    summary="Resend email verification for logged-in user"
)
async def resend_verification_email(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Resend email verification for the currently authenticated user.
    """
    if current_user.email_verified:
        return SendVerificationResponse(
            message="Email is already verified."
        )

    # Generate verification token and link
    verification_token = create_verification_token(
        user_id=str(current_user.id),
        email=current_user.email,
        purpose="email_verification"
    )
    verification_link = generate_verification_link(verification_token)

    # Send verification email
    email_service.send_email_verification(
        background_tasks=background_tasks,
        email_to=current_user.email,
        name=current_user.username,
        verification_link=verification_link
    )

    return SendVerificationResponse(
        message="Verification email has been sent."
    )


# ============================================
# Password Reset Endpoints
# ============================================

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request password reset"
)
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Request password reset email.

    - Finds user by email
    - Generates password reset token
    - Sends password reset email
    """
    user = await get_user_by_email(db, request.email)

    if not user:
        # Don't reveal if email exists for security
        return ForgotPasswordResponse(
            message="If this email is registered, a password reset link has been sent."
        )

    # Generate reset token and link
    reset_token = create_verification_token(
        user_id=str(user.id),
        email=user.email,
        purpose="password_reset"
    )
    reset_link = generate_password_reset_link(reset_token)

    # Send password reset email
    email_service.send_password_reset_email(
        background_tasks=background_tasks,
        email_to=user.email,
        name=user.username,
        reset_link=reset_link
    )

    return ForgotPasswordResponse(
        message="If this email is registered, a password reset link has been sent."
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="Reset password with token"
)
async def reset_password(
    request: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Reset user's password using reset token.

    - Validates the reset token
    - Updates password
    - Sends password change notification
    """
    user = await reset_user_password(
        db=db,
        token=request.token,
        new_password=request.new_password
    )

    # Send password change notification
    email_service.send_password_change_notice(
        background_tasks=background_tasks,
        email_to=user.email,
        name=user.username
    )

    return ResetPasswordResponse(
        message="Password has been reset successfully."
    )


# ============================================
# Current User Endpoint
# ============================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user"
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the currently authenticated user's profile.
    """
    return UserResponse.model_validate(current_user)


# ============================================
# Google OAuth Endpoints
# ============================================

@router.post(
    "/google/login",
    response_model=LoginResponse,
    summary="Login with Google OAuth"
)
async def google_login(
    token: GoogleCallBack,
    db: AsyncSession = Depends(get_session)
):
    """
    Authenticate user via Google OAuth and return JWT access token.

    - Verifies Google ID token
    - Validates user exists in the system
    - Returns JWT token for authenticated requests
    """
    user, access_token, expires_in = await google_callback_login(
        token=token,
        db=db
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/google/signup",
    response_model=LoginResponse,
    summary="Sign up with Google OAuth",
    status_code=status.HTTP_201_CREATED
)
async def google_signup(
    token: GoogleCallBack,
    db: AsyncSession = Depends(get_session)
):
    """
    Create a new user account via Google OAuth and return JWT access token.

    - Verifies Google ID token
    - Creates new user account with Google authentication
    - Email is automatically verified (Google provides verified emails)
    - Returns JWT token for immediate authenticated access
    """
    user, access_token, expires_in = await google_callback_signup(
        token=token,
        db=db
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )
