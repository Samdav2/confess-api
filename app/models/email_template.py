from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import Column, DateTime, JSON, Text
from sqlmodel import SQLModel, Field


class AdminEmailTemplate(SQLModel, table=True):
    __tablename__ = "admin_email_templates"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False, max_length=255)
    category: str = Field(default="custom", max_length=50, index=True)
    subject: str = Field(nullable=False, max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    html_content: str = Field(sa_column=Column(Text, nullable=False))
    cta_text: Optional[str] = Field(default=None, max_length=100)
    cta_link: Optional[str] = Field(default=None, max_length=500)
    image_urls: Optional[List[str]] = Field(
        default=None, sa_column=Column("image_urls", JSON, nullable=True)
    )
    created_by: UUID = Field(foreign_key="admins.id", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            onupdate=lambda: datetime.now(timezone.utc),
        ),
        default_factory=lambda: datetime.now(timezone.utc),
    )
