from typing import Optional
from uuid import UUID
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.campaign import EmailCampaign, CampaignStatus


class CampaignRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, campaign: EmailCampaign) -> EmailCampaign:
        self.session.add(campaign)
        await self.session.commit()
        await self.session.refresh(campaign)
        return campaign

    async def get_by_id(self, campaign_id: UUID) -> Optional[EmailCampaign]:
        stmt = select(EmailCampaign).where(EmailCampaign.id == campaign_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def get_all(
        self, skip: int = 0, limit: int = 50
    ) -> tuple[list[EmailCampaign], int]:
        count_stmt = select(func.count()).select_from(EmailCampaign)
        count_result = await self.session.exec(count_stmt)
        total = count_result.one() or 0

        stmt = (
            select(EmailCampaign)
            .order_by(EmailCampaign.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return list(result.all()), total

    async def update(self, campaign: EmailCampaign) -> EmailCampaign:
        self.session.add(campaign)
        await self.session.commit()
        await self.session.refresh(campaign)
        return campaign

    async def delete(self, campaign_id: UUID) -> bool:
        campaign = await self.get_by_id(campaign_id)
        if not campaign:
            return False
        await self.session.delete(campaign)
        await self.session.commit()
        return True

    async def get_recipient_count(self) -> int:
        from app.models.user import User
        stmt = select(func.count()).select_from(User).where(User.email_verified == True)
        result = await self.session.exec(stmt)
        return result.one()
