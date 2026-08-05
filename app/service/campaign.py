from typing import Optional
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


class CampaignService:
    async def create_campaign(
        self, session: AsyncSession, data: CampaignCreate, admin_id: UUID
    ) -> EmailCampaign:
        campaign = EmailCampaign(
            subject=data.subject,
            preview_text=data.preview_text,
            html_content=data.html_content,
            sender_name=data.sender_name,
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
    ) -> tuple[list[EmailCampaign], int]:
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
            )

        campaign.status = CampaignStatus.SENT
        campaign.sent_count = len(users)
        campaign.sent_at = datetime.now(timezone.utc)
        return await repo.update(campaign)

    async def get_recipient_count(self, session: AsyncSession) -> int:
        repo = CampaignRepository(session)
        return await repo.get_recipient_count()


campaign_service = CampaignService()
