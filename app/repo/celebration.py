from typing import Optional, List, Tuple
from uuid import UUID
from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.models.celebration import CelebrationPage, OccasionType, PaymentStatus

class CelebrationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, celebration: CelebrationPage) -> CelebrationPage:
        self.session.add(celebration)
        await self.session.commit()
        await self.session.refresh(celebration)
        return celebration

    async def get_by_id(self, celebration_id: UUID) -> Optional[CelebrationPage]:
        statement = select(CelebrationPage).where(CelebrationPage.id == celebration_id)
        result = await self.session.exec(statement)
        return result.first()

    async def get_by_slug(self, slug: str) -> Optional[CelebrationPage]:
        statement = select(CelebrationPage).where(CelebrationPage.slug == slug)
        result = await self.session.exec(statement)
        return result.first()

    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[CelebrationPage], int]:
        statement = select(CelebrationPage).where(CelebrationPage.created_by == user_id)

        # Get total count
        count_statement = select(func.count()).select_from(CelebrationPage).where(CelebrationPage.created_by == user_id)
        count_result = await self.session.exec(count_statement)
        total = count_result.one()

        # Get paginated results
        statement = statement.order_by(CelebrationPage.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.exec(statement)
        results = result.all()

        return results, total

    async def update_status(self, celebration_id: UUID, status: PaymentStatus) -> Optional[CelebrationPage]:
        celebration = await self.get_by_id(celebration_id)
        if not celebration:
            return None

        celebration.payment_status = status
        celebration.updated_at = datetime.now(timezone.utc)
        self.session.add(celebration)
        await self.session.commit()
        await self.session.refresh(celebration)
        return celebration

    async def delete(self, celebration_id: UUID) -> bool:
        celebration = await self.get_by_id(celebration_id)
        if not celebration:
            return False

        await self.session.delete(celebration)
        await self.session.commit()
        return True
