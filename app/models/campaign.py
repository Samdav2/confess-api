from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum
from sqlalchemy import Column, DateTime, JSON, Text
from sqlmodel import SQLModel, Field


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    SENDING = "sending"
    SENT = "sent"
    CANCELLED = "cancelled"


class EmailCampaign(SQLModel, table=True):
    __tablename__ = "email_campaigns"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    subject: str = Field(nullable=False, max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    html_content: str = Field(sa_column=Column(Text, nullable=False))
    sender_name: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default=CampaignStatus.DRAFT, max_length=50, index=True)
    recipient_filter: Optional[dict] = Field(default=None, sa_column=Column("recipient_filter", JSON, nullable=True))
    total_recipients: int = Field(default=0)
    sent_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    created_by: UUID = Field(foreign_key="admins.id", nullable=False)
    scheduled_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    sent_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(timezone.utc)),
        default_factory=lambda: datetime.now(timezone.utc)
    )
