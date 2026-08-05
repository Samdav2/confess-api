from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CampaignCreate(BaseModel):
    subject: Optional[str] = Field(default=None, max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=500, description="Alias for preview_text")
    html_content: Optional[str] = Field(default=None, description="HTML body content")
    email_content: Optional[str] = Field(default=None, description="Alias for html_content")
    sender_name: Optional[str] = Field(default=None, max_length=255)
    template_type: Optional[str] = Field(default="promotional", max_length=50)
    cta_link: Optional[str] = Field(default=None, max_length=500)
    cta_text: Optional[str] = Field(default=None, max_length=100)
    scheduled_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_aliases(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if "description" in values and not values.get("preview_text"):
                values["preview_text"] = values["description"]
            if "email_content" in values and not values.get("html_content"):
                values["html_content"] = values["email_content"]
        return values


class CampaignUpdate(BaseModel):
    subject: Optional[str] = Field(default=None, max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=500, description="Alias for preview_text")
    html_content: Optional[str] = Field(default=None)
    email_content: Optional[str] = Field(default=None, description="Alias for html_content")
    sender_name: Optional[str] = Field(default=None, max_length=255)
    template_type: Optional[str] = Field(default=None, max_length=50)
    cta_link: Optional[str] = Field(default=None, max_length=500)
    cta_text: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_aliases(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if "description" in values and not values.get("preview_text"):
                values["preview_text"] = values["description"]
            if "email_content" in values and not values.get("html_content"):
                values["html_content"] = values["email_content"]
        return values


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


class EmailTemplateResponse(BaseModel):
    id: str
    name: str
    category: str
    subject: str
    preview_text: str
    html_content: str
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None


class EmailTemplateListResponse(BaseModel):
    total: int
    templates: List[EmailTemplateResponse]
