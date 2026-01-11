from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field
from typing import Optional, List
from uuid import UUID, uuid4



class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    referred_by: str = Field(index=True)
    referral_code: str = Field(index=True, unique=True)
    email_verified: bool = Field(default=False, index=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )