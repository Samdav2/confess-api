from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ---------------------------------------------------------------------------
# Campaign Management (Admin CRUD)
# ---------------------------------------------------------------------------

class CampaignCreate(BaseModel):
    """Create a new email campaign."""

    subject: Optional[str] = Field(
        default=None, max_length=255,
        description="Email subject line. Auto-filled from template if omitted.",
    )
    preview_text: Optional[str] = Field(
        default=None, max_length=500,
        description="Inbox preview / preheader text. Auto-filled from template if omitted.",
    )
    html_content: Optional[str] = Field(
        default=None,
        description="Email body content. Auto-filled from template if omitted.",
    )
    sender_name: Optional[str] = Field(
        default=None, max_length=255,
        description="Display name for the sender (e.g. 'Confess Team')",
    )
    template_type: Optional[str] = Field(
        default="promotional", max_length=50,
        description="Pre-designed template slug or custom template UUID to auto-fill defaults",
    )
    cta_link: Optional[str] = Field(
        default=None, max_length=500,
        description="Call-to-action button URL. Auto-filled from template if omitted.",
    )
    cta_text: Optional[str] = Field(
        default=None, max_length=100,
        description="Call-to-action button label. Auto-filled from template if omitted.",
    )
    scheduled_at: Optional[datetime] = Field(
        default=None, description="Schedule campaign for future delivery (UTC)",
    )


class CampaignUpdate(BaseModel):
    """Partially update an existing campaign."""

    subject: Optional[str] = Field(default=None, max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    html_content: Optional[str] = None
    sender_name: Optional[str] = Field(default=None, max_length=255)
    template_type: Optional[str] = Field(default=None, max_length=50)
    cta_link: Optional[str] = Field(default=None, max_length=500)
    cta_text: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject: str
    preview_text: Optional[str] = None
    html_content: str
    sender_name: Optional[str] = None
    template_type: Optional[str] = "promotional"
    cta_link: Optional[str] = None
    cta_text: Optional[str] = None
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
    items: List[CampaignResponse]


class CampaignSendRequest(BaseModel):
    confirm: bool = Field(default=False, description="Must be True to confirm sending")
