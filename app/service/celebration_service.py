from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.celebration import CelebrationPage, MusicType, PaymentStatus
from app.schemas.celebration import CelebrationPageCreate, CelebrationPageUpdate
from app.repo.celebration import CelebrationRepository
from app.service.paystack_service import paystack_service
import re

class CelebrationService:
    def __init__(self, session: AsyncSession):
        self.repository = CelebrationRepository(session)
        self.session = session

    def validate_slug(self, slug: str) -> bool:
        """
        Rules:
        - Lowercase only
        - No spaces
        - Hyphen allowed
        - 3 – 40 characters
        - Unique (checked separately)
        """
        if not (3 <= len(slug) <= 40):
            return False
        if not re.match(r'^[a-z0-9-]+$', slug):
            return False
        return True

    async def check_slug_availability(self, slug: str) -> bool:
        if not self.validate_slug(slug):
            return False
        existing = await self.repository.get_by_slug(slug)
        return existing is None

    def calculate_price(self, image_count: int, music_type: MusicType) -> float:
        """
        Formula:
        base_price = 1000 (up to 3 images)
        if images > 3:
            extra_images = images - 3
            extra_cost = extra_images * 500

        Music:
        None: 0
        App Music: 200
        Custom Music: 500
        """
        base_price = 1000
        extra_image_cost = 0
        if image_count > 3:
            extra_image_cost = (image_count - 3) * 500

        music_cost = 0
        if music_type == MusicType.APP_MUSIC:
            music_cost = 200
        elif music_type == MusicType.CUSTOM_MUSIC:
            music_cost = 500

        return float(base_price + extra_image_cost + music_cost)

    async def create_celebration_page(self, user_id: UUID, data: CelebrationPageCreate) -> CelebrationPage:
        # Validate slug
        if not self.validate_slug(data.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid slug format. Use 3-40 lowercase characters, numbers or hyphens."
            )

        if not await self.check_slug_availability(data.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug already taken."
            )

        total_price = self.calculate_price(len(data.images), data.music_type)

        celebration = CelebrationPage(
            **data.model_dump(),
            created_by=user_id,
            total_price=total_price,
            payment_status=PaymentStatus.PENDING
        )

        return await self.repository.create(celebration)

    async def get_celebration_by_slug(self, slug: str) -> CelebrationPage:
        celebration = await self.repository.get_by_slug(slug)
        if not celebration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Celebration page not found."
            )
        return celebration

    async def get_user_celebrations(self, user_id: UUID, page: int = 1, page_size: int = 10) -> Tuple[List[CelebrationPage], int]:
        skip = (page - 1) * page_size
        return await self.repository.get_by_user_id(user_id, skip, page_size)

    async def initialize_payment(self, celebration_id: UUID, user_id: UUID, email: str, callback_url: Optional[str] = None):
        celebration = await self.repository.get_by_id(celebration_id)
        if not celebration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Celebration page not found")

        if celebration.created_by != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        if celebration.payment_status == PaymentStatus.PAID:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already paid")

        return await paystack_service.initialize_transaction(
            session=self.session,
            user_id=str(user_id),
            email=email,
            amount=celebration.total_price,
            callback_url=callback_url,
            celebration_id=str(celebration_id)
        )
