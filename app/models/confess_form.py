from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from enum import Enum


class ConfessType(str, Enum):
    DINNER_DATE = "dinner_date"
    ANONYMOUS = "anonymous"
    APPRECIATION = "appreciation"

class DeliveryMethod(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"

class ConfessForm(SQLModel, table=True):
    __tablename__ = 'confess_forms'
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    confess_type: ConfessType = Field(default=ConfessType.DINNER_DATE, nullable=False, index=True)
    tone: str = Field(nullable=False, index=True)
    message: str = Field(nullable=False)
    anonymous: bool = Field(nullable=False, default=False)
    card_design: int = Field(nullable=False, default=0)
    delivery: DeliveryMethod = Field(nullable=False, default=DeliveryMethod.EMAIL, index=True)
    email: str = Field(nullable=True, index=True)
    phone: str = Field(nullable=True, index=True)
    name: str = Field(nullable=True, index=True)
    paid: bool = Field(default=True, nullable=True)
    slug: str = Field(nullable=True, index=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    user: "User" = Relationship(back_populates="confess_forms")

