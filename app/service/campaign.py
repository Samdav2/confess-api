from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import BackgroundTasks

from app.models.campaign import EmailCampaign, CampaignStatus
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from app.repo.campaign import CampaignRepository
from app.dependencies.email_service import EmailService
from app.models.user import User
from sqlmodel import select
from app.constants.email_templates import (
    get_all_templates,
    get_template_by_id,
    EmailTemplatePreset,
)


class CampaignService:
    def list_templates(self) -> List[EmailTemplatePreset]:
        return get_all_templates()

    def get_template(self, template_id: str) -> Optional[EmailTemplatePreset]:
        return get_template_by_id(template_id)

    async def create_campaign(
        self, session: AsyncSession, data: CampaignCreate, admin_id: UUID
    ) -> EmailCampaign:
        template_type = data.template_type or "promotional"
        preset = get_template_by_id(template_type)

        subject = data.subject or (preset.subject if preset else "Notification from Confess")
        preview_text = data.preview_text or (preset.preview_text if preset else None)
        html_content = data.html_content or (preset.html_content if preset else "<p>No content provided</p>")
        cta_link = data.cta_link or (preset.cta_link if preset else None)
        cta_text = data.cta_text or (preset.cta_text if preset else None)

        campaign = EmailCampaign(
            subject=subject,
            preview_text=preview_text,
            html_content=html_content,
            sender_name=data.sender_name,
            template_type=template_type,
            cta_link=cta_link,
            cta_text=cta_text,
            created_by=admin_id,
            scheduled_at=data.scheduled_at,
        )
        repo = CampaignRepository(session)
        return await repo.create(campaign)

    async def get_campaign(
        self, session: AsyncSession, campaign_id: UUID
    ) -> Optional[EmailCampaign]:
        repo = CampaignRepository(session)
        return await repo.get_by_id(campaign_id)

    async def list_campaigns(
        self, session: AsyncSession, skip: int = 0, limit: int = 50
    ) -> Tuple[List[EmailCampaign], int]:
        repo = CampaignRepository(session)
        return await repo.get_all(skip=skip, limit=limit)

    async def update_campaign(
        self, session: AsyncSession, campaign_id: UUID, data: CampaignUpdate
    ) -> Optional[EmailCampaign]:
        repo = CampaignRepository(session)
        campaign = await repo.get_by_id(campaign_id)
        if not campaign:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "description" in update_data:
            del update_data["description"]
        if "email_content" in update_data:
            del update_data["email_content"]

        if "status" in update_data and update_data["status"] not in [
            s.value for s in CampaignStatus
        ]:
            del update_data["status"]

        for key, value in update_data.items():
            setattr(campaign, key, value)
        campaign.updated_at = datetime.now(timezone.utc)

        return await repo.update(campaign)

    async def delete_campaign(
        self, session: AsyncSession, campaign_id: UUID
    ) -> bool:
        repo = CampaignRepository(session)
        return await repo.delete(campaign_id)

    async def send_campaign(
        self,
        session: AsyncSession,
        campaign_id: UUID,
        background_tasks: BackgroundTasks,
    ) -> Optional[EmailCampaign]:
        repo = CampaignRepository(session)
        campaign = await repo.get_by_id(campaign_id)
        if not campaign:
            return None

        campaign.status = CampaignStatus.SENDING
        await repo.update(campaign)

        stmt = select(User).where(User.email_verified == True)
        result = await session.exec(stmt)
        users = list(result.all())

        campaign.total_recipients = len(users)
        await repo.update(campaign)

        sender_name = campaign.sender_name or "Confess Team"

        for user in users:
            background_tasks.add_task(
                EmailService._send_campaign_email,
                subject=campaign.subject,
                email_to=user.email,
                name=user.username,
                html_content=campaign.html_content,
                preview_text=campaign.preview_text or "",
                sender_name=sender_name,
                campaign_id=campaign.id,
                cta_link=campaign.cta_link,
                cta_text=campaign.cta_text,
            )

        campaign.status = CampaignStatus.SENT
        campaign.sent_count = len(users)
        campaign.sent_at = datetime.now(timezone.utc)
        return await repo.update(campaign)

    async def get_recipient_count(self, session: AsyncSession) -> int:
        repo = CampaignRepository(session)
        return await repo.get_recipient_count()


campaign_service = CampaignService()
