from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from typing import List, Optional



class User(SQLModel, table=True):
    __tablename__ = "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(unique=False, index=True)
    email: str = Field(unique=True, index=True)
    password: str = Field(nullable=False)
    referred_by: Optional[str] = Field(default=None, index=True, nullable=True)
    referral_code: str = Field(index=True, unique=True)
    email_verified: bool = Field(default=False, index=True)
    google_auth: bool = Field(default=False, nullable=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    confess_forms: Optional[List["ConfessForm"]] = Relationship(back_populates="user")