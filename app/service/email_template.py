from typing import Optional, List, Union
from uuid import UUID
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.email_template import AdminEmailTemplate
from app.schemas.email_template import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
)
from app.repo.email_template import EmailTemplateRepository
from app.constants.email_templates import get_all_templates, get_template_by_id
from app.dependencies.email_service import EmailService
from app.config.settings import settings


class EmailTemplateService:
    async def create_custom_template(
        self, session: AsyncSession, data: EmailTemplateCreate, admin_id: UUID
    ) -> AdminEmailTemplate:
        template = AdminEmailTemplate(
            name=data.name,
            category=data.category or "custom",
            subject=data.subject,
            preview_text=data.preview_text,
            html_content=data.html_content,
            cta_text=data.cta_text,
            cta_link=data.cta_link,
            image_urls=data.image_urls,
            created_by=admin_id,
        )
        repo = EmailTemplateRepository(session)
        return await repo.create(template)

    async def list_all_templates(
        self, session: AsyncSession, skip: int = 0, limit: int = 50
    ) -> tuple[List[EmailTemplateResponse], int]:
        repo = EmailTemplateRepository(session)
        custom_templates, total_custom = await repo.get_all(skip=skip, limit=limit)

        predesigned = get_all_templates()
        response_list: List[EmailTemplateResponse] = []

        # Pre-designed templates first
        for p in predesigned:
            response_list.append(
                EmailTemplateResponse(
                    id=p.id,
                    name=p.name,
                    category=p.category,
                    subject=p.subject,
                    preview_text=p.preview_text,
                    html_content=p.html_content,
                    cta_text=p.cta_text,
                    cta_link=p.cta_link,
                    is_predesigned=True,
                )
            )

        # Custom templates from DB
        for c in custom_templates:
            response_list.append(
                EmailTemplateResponse(
                    id=c.id,
                    name=c.name,
                    category=c.category,
                    subject=c.subject,
                    preview_text=c.preview_text,
                    html_content=c.html_content,
                    cta_text=c.cta_text,
                    cta_link=c.cta_link,
                    image_urls=c.image_urls,
                    is_predesigned=False,
                    created_by=c.created_by,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )

        total = len(predesigned) + total_custom
        return response_list, total

    async def get_template_by_id(
        self, session: AsyncSession, template_id: Union[str, UUID]
    ) -> Optional[EmailTemplateResponse]:
        # Check pre-defined first
        template_id_str = str(template_id)
        preset = get_template_by_id(template_id_str)
        if preset:
            return EmailTemplateResponse(
                id=preset.id,
                name=preset.name,
                category=preset.category,
                subject=preset.subject,
                preview_text=preset.preview_text,
                html_content=preset.html_content,
                cta_text=preset.cta_text,
                cta_link=preset.cta_link,
                is_predesigned=True,
            )

        # Check DB for custom template by UUID
        try:
            uuid_id = UUID(template_id_str)
            repo = EmailTemplateRepository(session)
            c = await repo.get_by_id(uuid_id)
            if c:
                return EmailTemplateResponse(
                    id=c.id,
                    name=c.name,
                    category=c.category,
                    subject=c.subject,
                    preview_text=c.preview_text,
                    html_content=c.html_content,
                    cta_text=c.cta_text,
                    cta_link=c.cta_link,
                    image_urls=c.image_urls,
                    is_predesigned=False,
                    created_by=c.created_by,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
        except ValueError:
            pass

        return None

    async def update_custom_template(
        self, session: AsyncSession, template_id: UUID, data: EmailTemplateUpdate
    ) -> Optional[AdminEmailTemplate]:
        repo = EmailTemplateRepository(session)
        template = await repo.get_by_id(template_id)
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(template, key, value)
        template.updated_at = datetime.now(timezone.utc)

        return await repo.update(template)

    async def delete_custom_template(
        self, session: AsyncSession, template_id: UUID
    ) -> bool:
        repo = EmailTemplateRepository(session)
        return await repo.delete(template_id)

    async def render_template_preview(
        self,
        session: AsyncSession,
        template_id: Union[str, UUID],
        recipient_name: str = "Valued User",
        custom_subject: Optional[str] = None,
        custom_preview_text: Optional[str] = None,
        custom_html_content: Optional[str] = None,
        custom_cta_text: Optional[str] = None,
        custom_cta_link: Optional[str] = None,
    ) -> str:
        t = await self.get_template_by_id(session, template_id)
        if not t and not custom_html_content:
            raise ValueError(f"Template '{template_id}' not found")

        subject = custom_subject or (t.subject if t else "Sample Email Subject")
        preview_text = custom_preview_text or (t.preview_text if t else "")
        html_content = custom_html_content or (t.html_content if t else "<p>Sample Content</p>")
        cta_text = custom_cta_text or (t.cta_text if t else None)
        cta_link = custom_cta_link or (t.cta_link if t else None)

        context = {
            "name": recipient_name,
            "html_content": html_content,
            "preview_text": preview_text,
            "sender_name": "Confess Team",
            "project_name": settings.PROJECT_NAME,
            "subject": subject,
            "site_url": settings.FRONTEND_URL,
            "current_year": datetime.now().year,
            "cta_link": cta_link,
            "cta_text": cta_text,
        }

        return EmailService._render_template("promotional_email.html", context)


email_template_service = EmailTemplateService()
