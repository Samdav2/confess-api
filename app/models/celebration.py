from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, JSON, Float, String, Enum as SAEnum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from enum import Enum

class OccasionType(str, Enum):
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    PROPOSAL = "proposal"
    GRADUATION = "graduation"
    VALENTINE = "valentine"
    APPRECIATION = "appreciation"
    CUSTOM = "custom"

class MusicType(str, Enum):
    NONE = "none"
    APP_MUSIC = "app_music"
    CUSTOM_MUSIC = "custom_music"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"

class CelebrationPage(SQLModel, table=True):
    __tablename__ = 'celebration_pages'
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    slug: str = Field(unique=True, index=True, nullable=False)
    recipient_name: str = Field(nullable=False)
    occasion_type: OccasionType = Field(sa_column=Column(SAEnum(OccasionType), nullable=False, index=True))
    images: List[str] = Field(sa_column=Column(JSON, nullable=False, default=[]))
    music_type: MusicType = Field(sa_column=Column(SAEnum(MusicType), nullable=False, default=MusicType.NONE))
    music_url: Optional[str] = Field(default=None)
    created_by: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    total_price: float = Field(sa_column=Column(Float, nullable=False))
    payment_status: PaymentStatus = Field(
        sa_column=Column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    user: "User" = Relationship(back_populates="celebration_pages")
