from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class FeedbackCreate(BaseModel):
    message: str
    rating: int = Field(ge=1, le=5)

class FeedbackResponse(BaseModel):
    id: UUID
    name: str
    message: str
    rating: int
    created_at: datetime
