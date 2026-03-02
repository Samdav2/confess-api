from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class AdminCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=8)
    is_super_admin: bool = False

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    is_super_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class AdminPasswordReset(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8)

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin: AdminResponse

class DashboardStatsResponse(BaseModel):
    total_users: int
    total_confess_forms: int
    total_anonymous_links: int
    total_messages: int
