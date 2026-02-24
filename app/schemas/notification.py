from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    content: str
    is_read: bool
    read_at: Optional[datetime] = None
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    metadata_: Optional[dict] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    notifications: List[NotificationResponse]


class MarkReadRequest(BaseModel):
    notification_ids: List[UUID]
