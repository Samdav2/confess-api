from datetime import datetime, timezone
from sqlalchemy import DateTime, Column
from sqlmodel import SQLModel, Field
from typing import Optional, List
from uuid import UUID, uuid4



class Waitlist(SQLModel, table=True):
    __tablename__ = "waitlists"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
