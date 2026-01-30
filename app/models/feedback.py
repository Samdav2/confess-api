from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4

class Feedback(SQLModel, table=True):
    __tablename__ = "feedbacks"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    message: str = Field(nullable=False)
    rating: int = Field(nullable=False)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    user: Optional["User"] = Relationship(back_populates="feedbacks")
