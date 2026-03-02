from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4


class Admin(SQLModel, table=True):
    __tablename__ = "admins"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(unique=False, index=True)
    email: str = Field(unique=True, index=True)
    password: str = Field(nullable=False)
    is_super_admin: bool = Field(default=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
