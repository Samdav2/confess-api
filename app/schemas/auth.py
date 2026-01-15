from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr

class TokenData(BaseModel):
    """Schema for decoded token data"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    exp: Optional[datetime] = None


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Schema for token payload"""
    sub: str  # user_id
    email: str
    exp: datetime
    iat: datetime


class LoginRequest(BaseModel):
    """Request schema for user login"""
    email: EmailStr
    password: str = Field(min_length=6)


class LoginResponse(BaseModel):
    """Response schema for successful login"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"

class SignupRequest(BaseModel):
    """Request schema for user registration"""
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)
    referred_by: Optional[str] = None


class SignupResponse(BaseModel):
    """Response schema for successful registration"""
    message: str
    user: "UserResponse"

class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password"""
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Response schema for forgot password"""
    message: str


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset"""
    token: str
    new_password: str = Field(min_length=6)


class ResetPasswordResponse(BaseModel):
    """Response schema for password reset"""
    message: str


class SendVerificationRequest(BaseModel):
    """Request schema for sending email verification"""
    email: EmailStr


class SendVerificationResponse(BaseModel):
    """Response schema for sending email verification"""
    message: str


class VerifyEmailRequest(BaseModel):
    """Request schema for email verification via token"""
    token: str


class VerifyEmailResponse(BaseModel):
    """Response schema for email verification"""
    message: str
    email_verified: bool


class UserResponse(BaseModel):
    """User data returned in auth responses"""
    id: UUID
    username: str
    email: str
    email_verified: bool
    referral_code: str
    created_at: datetime

    class Config:
        from_attributes = True


class GoogleCallBack(BaseModel):
    id_token: str

    class Config:
        from_attributes = True

LoginResponse.model_rebuild()
SignupResponse.model_rebuild()
