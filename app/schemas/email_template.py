from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID


class EmailTemplateCreate(BaseModel):
    name: str = Field(..., max_length=255)
    category: Optional[str] = Field(default="custom", max_length=50)
    subject: str = Field(..., max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=500, description="Alias for preview_text")
    html_content: Optional[str] = Field(default=None, description="HTML body content")
    email_content: Optional[str] = Field(default=None, description="Alias for html_content")
    cta_text: Optional[str] = Field(default=None, max_length=100)
    cta_link: Optional[str] = Field(default=None, max_length=500)
    image_urls: Optional[List[str]] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_aliases(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if "description" in values and not values.get("preview_text"):
                values["preview_text"] = values["description"]
            if "email_content" in values and not values.get("html_content"):
                values["html_content"] = values["email_content"]
        return values


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=50)
    subject: Optional[str] = Field(default=None, max_length=255)
    preview_text: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=500, description="Alias for preview_text")
    html_content: Optional[str] = Field(default=None)
    email_content: Optional[str] = Field(default=None, description="Alias for html_content")
    cta_text: Optional[str] = Field(default=None, max_length=100)
    cta_link: Optional[str] = Field(default=None, max_length=500)
    image_urls: Optional[List[str]] = None

    @model_validator(mode="before")
    @classmethod
    def resolve_aliases(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if "description" in values and not values.get("preview_text"):
                values["preview_text"] = values["description"]
            if "email_content" in values and not values.get("html_content"):
                values["html_content"] = values["email_content"]
        return values


class CustomEmailTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Union[UUID, str]
    name: str
    category: str
    subject: str
    preview_text: Optional[str] = None
    description: Optional[str] = None
    html_content: str
    email_content: Optional[str] = None
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None
    image_urls: Optional[List[str]] = None
    is_predesigned: bool = False
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def populate_convenience_aliases(cls, values: dict) -> dict:
        if isinstance(values, dict):
            if not values.get("description") and values.get("preview_text"):
                values["description"] = values["preview_text"]
            if not values.get("email_content") and values.get("html_content"):
                values["email_content"] = values["html_content"]
        elif hasattr(values, "__dict__"):
            # Model object
            if not getattr(values, "description", None):
                values.description = getattr(values, "preview_text", None)
            if not getattr(values, "email_content", None):
                values.email_content = getattr(values, "html_content", None)
        return values


class CustomEmailTemplateListResponse(BaseModel):
    total: int
    templates: List[CustomEmailTemplateResponse]


class EmailTemplatePreviewRequest(BaseModel):
    sample_name: Optional[str] = Field(default="John Doe")
    subject: Optional[str] = None
    preview_text: Optional[str] = None
    html_content: Optional[str] = None
    cta_text: Optional[str] = None
    cta_link: Optional[str] = None


class EmailTemplatePreviewResponse(BaseModel):
    rendered_html: str
