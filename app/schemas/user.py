from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(min_length=1)
    email: str = Field(pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    referred_by: Optional[str] = None
    referral_code: Optional[str] = None


class UserCreate(UserBase):
    password: str
    pass


class UserRead(UserBase):
    id: UUID
    referral_code: str
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    referral_code: str
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserGoogleCreate(UserBase):
    google_auth: bool = True

    class Config:
        from_attributes = True
