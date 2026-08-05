from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from typing import Union

from app.db.sessions import get_session
from app.dependencies.auth import get_current_admin
from app.models.admin import Admin
from app.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
    CustomEmailTemplateResponse,
    CustomEmailTemplateListResponse,
    EmailTemplatePreviewRequest,
    EmailTemplatePreviewResponse,
)
from app.service.email_template import email_template_service

router = APIRouter()


@router.get("", response_model=CustomEmailTemplateListResponse)
async def list_email_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    templates, total = await email_template_service.list_all_templates(
        session=session, skip=skip, limit=limit
    )
    return CustomEmailTemplateListResponse(total=total, templates=templates)


@router.post(
    "", response_model=CustomEmailTemplateResponse, status_code=status.HTTP_201_CREATED
)
async def create_custom_template(
    request: EmailTemplateCreate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    created = await email_template_service.create_custom_template(
        session=session, data=request, admin_id=current_admin.id
    )
    fetched = await email_template_service.get_template_by_id(session, created.id)
    return fetched


@router.get("/{template_id}", response_model=CustomEmailTemplateResponse)
async def get_email_template(
    template_id: str,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    template = await email_template_service.get_template_by_id(
        session=session, template_id=template_id
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email template '{template_id}' not found",
        )
    return template


@router.patch("/{template_id}", response_model=CustomEmailTemplateResponse)
async def update_custom_template(
    template_id: UUID,
    request: EmailTemplateUpdate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    updated = await email_template_service.update_custom_template(
        session=session, template_id=template_id, data=request
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom template not found or is pre-defined",
        )
    fetched = await email_template_service.get_template_by_id(session, updated.id)
    return fetched


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_template(
    template_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
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
    try:
        html = await email_template_service.render_template_preview(
            session=session,
            template_id=template_id,
            sample_name=request.sample_name or "Valued User",
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
