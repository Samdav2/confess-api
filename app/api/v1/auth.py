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
    VerifyEmailCodeRequest,
    VerifyEmailResponse,
    UserResponse,
    GoogleCallBack,
)
from app.service.auth import (
    login_user,
    verify_user_email_with_code,
    reset_user_password,
    get_user_by_email,
    generate_verification_code,
    store_verification_code,
    generate_password_reset_link,
    create_verification_token,
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
    summary="Send email verification code"
)
async def send_verification_email(
    request: SendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Send email verification code to user.

    - Finds user by email
    - Generates 6-digit verification code
    - Sends verification email with code
    """
    user = await get_user_by_email(db, request.email)

    if not user:
        # Don't reveal if email exists for security
        return SendVerificationResponse(
            message="If this email is registered, a verification code has been sent."
        )

    if user.email_verified:
        return SendVerificationResponse(
            message="Email is already verified."
        )

    # Generate and store verification code
    verification_code = generate_verification_code()
    store_verification_code(
        email=user.email,
        code=verification_code,
        user_id=str(user.id)
    )

    # Send verification email with code
    email_service.send_email_verification(
        background_tasks=background_tasks,
        email_to=user.email,
        name=user.username,
        verification_code=verification_code
    )

    return SendVerificationResponse(
        message="If this email is registered, a verification code has been sent."
    )


@router.post(
    "/verify-email",
    summary="Verify email with code"
)
async def verify_email(
    request: VerifyEmailCodeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    Verify user's email address using 6-digit verification code.

    - Validates the verification code
    - Marks email as verified
    - Sends confirmation email
    """
    response = await verify_user_email_with_code(db, str(request.email), request.code)
    user = response["user"]

    # Send verification success email
    email_service.send_email_verified_notice(
        background_tasks=background_tasks,
        email_to=user.email,
        name=user.username
    )

    return {"msg": VerifyEmailResponse(
        message="Email verified successfully!",
        email_verified=True
    ), "token": response["token"]}

@router.get(
    "/resend-verification",
    response_model=SendVerificationResponse,
    summary="Resend email verification code for logged-in user"
)
async def resend_verification_email(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Resend email verification code for the currently authenticated user.
    """
    if current_user.email_verified:
        return SendVerificationResponse(
            message="Email is already verified."
        )

    # Generate and store verification code
    verification_code = generate_verification_code()
    store_verification_code(
        email=current_user.email,
        code=verification_code,
        user_id=str(current_user.id)
    )

    # Send verification email with code
    email_service.send_email_verification(
        background_tasks=background_tasks,
        email_to=current_user.email,
        name=current_user.username,
        verification_code=verification_code
    )

    return SendVerificationResponse(
        message="Verification code has been sent to your email."
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
