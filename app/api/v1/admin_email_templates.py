from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from app.db.sessions import get_session
from app.dependencies.auth import get_current_admin
from app.models.admin import Admin
from app.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
    EmailTemplateListResponse,
    EmailTemplatePreviewRequest,
    EmailTemplatePreviewResponse,
)
from app.service.email_template import email_template_service

router = APIRouter()


@router.get("", response_model=EmailTemplateListResponse)
@router.get("/", response_model=EmailTemplateListResponse, include_in_schema=False)
async def list_email_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """List all email templates (pre-designed + custom)."""
    templates, total = await email_template_service.list_all_templates(
        session=session, skip=skip, limit=limit
    )
    return EmailTemplateListResponse(total=total, templates=templates)


@router.post(
    "", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED
)
@router.post(
    "/", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False
)
async def create_custom_template(
    request: EmailTemplateCreate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Create a new custom email template."""
    created = await email_template_service.create_custom_template(
        session=session, data=request, admin_id=current_admin.id
    )
    fetched = await email_template_service.get_template_by_id(session, created.id)
    return fetched


@router.get("/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_id: str,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Get details of a specific template (pre-designed or custom)."""
    template = await email_template_service.get_template_by_id(
        session=session, template_id=template_id
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email template '{template_id}' not found",
        )
    return template


@router.patch("/{template_id}", response_model=EmailTemplateResponse)
async def update_custom_template(
    template_id: UUID,
    request: EmailTemplateUpdate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Update a custom email template. Pre-designed templates cannot be modified."""
    updated = await email_template_service.update_custom_template(
        session=session, template_id=template_id, data=request
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom template not found or is a pre-designed template",
        )
    fetched = await email_template_service.get_template_by_id(session, updated.id)
    return fetched


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_template(
    template_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Delete a custom email template. Pre-designed templates cannot be deleted."""
    deleted = await email_template_service.delete_custom_template(
        session=session, template_id=template_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom template not found or cannot be deleted",
        )


@router.post("/{template_id}/preview", response_model=EmailTemplatePreviewResponse)
async def preview_email_template(
    template_id: str,
    request: EmailTemplatePreviewRequest = EmailTemplatePreviewRequest(),
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Render a full HTML preview of a template with sample data."""
    try:
        html = await email_template_service.render_template_preview(
            session=session,
            template_id=template_id,
            recipient_name=request.recipient_name,
            custom_subject=request.subject,
            custom_preview_text=request.preview_text,
            custom_html_content=request.html_content,
            custom_cta_text=request.cta_text,
            custom_cta_link=request.cta_link,
        )
        return EmailTemplatePreviewResponse(rendered_html=html)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
