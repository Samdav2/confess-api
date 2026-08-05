from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID


# ---------------------------------------------------------------------------
# Template Management (Admin CRUD)
# ---------------------------------------------------------------------------

class EmailTemplateCreate(BaseModel):
    """Create a new custom email template."""

    name: str = Field(..., max_length=255, description="Internal template name")
    category: str = Field(
        default="custom", max_length=50,
        description="Template category (e.g. custom, promotional, engagement, informational)",
    )
    subject: str = Field(..., max_length=255, description="Email subject line")
    preview_text: Optional[str] = Field(
        default=None, max_length=500,
        description="Inbox preview / preheader text shown alongside the subject",
    )
    html_content: str = Field(
        ..., description="Email body content (plain text or HTML markup)",
    )
    cta_text: Optional[str] = Field(
        default=None, max_length=100,
        description="Call-to-action button label",
    )
    cta_link: Optional[str] = Field(
        default=None, max_length=500,
        description="Call-to-action button URL",
    )
    image_urls: Optional[List[str]] = Field(
        default=None, description="Optional list of image URLs to embed",
    )


class EmailTemplateUpdate(BaseModel):
    """Partially update an existing custom email template."""

    name: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=50)
    subject: Optional[str] = Field(default=None, max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    html_content: Optional[str] = Field(default=None)
    cta_text: Optional[str] = Field(default=None, max_length=100)
    cta_link: Optional[str] = Field(default=None, max_length=500)
    image_urls: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class EmailTemplateResponse(BaseModel):
    """Unified response for both pre-designed and custom templates."""

    model_config = ConfigDict(from_attributes=True)

    id: Union[UUID, str] = Field(description="UUID for custom templates, string slug for pre-designed")
    name: str
    category: str
    subject: str
    preview_text: Optional[str] = None
    html_content: str
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None
    image_urls: Optional[List[str]] = None
    is_predesigned: bool = Field(
        default=False,
        description="True if this is a built-in preset template, False if admin-created",
    )
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EmailTemplateListResponse(BaseModel):
    total: int
    templates: List[EmailTemplateResponse]


# ---------------------------------------------------------------------------
# Template Preview
# ---------------------------------------------------------------------------

class EmailTemplatePreviewRequest(BaseModel):
    """Override template fields for a rendered HTML preview."""

    recipient_name: str = Field(default="John Doe", description="Sample recipient name for preview")
    subject: Optional[str] = Field(default=None, description="Override subject line")
    preview_text: Optional[str] = Field(default=None, description="Override preview text")
    html_content: Optional[str] = Field(default=None, description="Override email body content")
    cta_text: Optional[str] = Field(default=None, description="Override CTA button text")
    cta_link: Optional[str] = Field(default=None, description="Override CTA button URL")


class EmailTemplatePreviewResponse(BaseModel):
    rendered_html: str
