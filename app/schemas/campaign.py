from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class CampaignCreate(BaseModel):
    subject: str = Field(..., max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    html_content: str
    sender_name: Optional[str] = Field(default=None, max_length=255)
    scheduled_at: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    subject: Optional[str] = Field(default=None, max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    html_content: Optional[str] = None
    sender_name: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject: str
    preview_text: Optional[str] = None
    html_content: str
    sender_name: Optional[str] = None
    status: str
    recipient_filter: Optional[dict] = None
    total_recipients: int
    sent_count: int
    failed_count: int
    created_by: UUID
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(BaseModel):
    total: int
    items: list[CampaignResponse]


class CampaignSendRequest(BaseModel):
    confirm: bool = Field(default=False, description="Must be True to confirm sending")
