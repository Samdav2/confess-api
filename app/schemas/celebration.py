from pydantic import BaseModel, Field as PydanticField
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.models.celebration import OccasionType, MusicType, PaymentStatus

class CelebrationPageBase(BaseModel):
    slug: str
    recipient_name: str
    occasion_type: OccasionType
    images: List[str] = []
    music_type: MusicType = MusicType.NONE
    music_url: Optional[str] = None

class CelebrationPageCreate(CelebrationPageBase):
    pass

class CelebrationPageUpdate(BaseModel):
    recipient_name: Optional[str] = None
    occasion_type: Optional[OccasionType] = None
    images: Optional[List[str]] = None
    music_type: Optional[MusicType] = None
    music_url: Optional[str] = None

class CelebrationPageResponse(CelebrationPageBase):
    id: UUID
    created_by: UUID
    total_price: float
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SlugAvailabilityResponse(BaseModel):
    available: bool

class CelebrationPageListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CelebrationPageResponse]
