from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.db.sessions import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.celebration import (
    CelebrationPageCreate,
    CelebrationPageResponse,
    CelebrationPageListResponse,
    SlugAvailabilityResponse
)
from app.service.celebration_service import CelebrationService
from app.schemas.paystack import PaystackInitializeRequest, PaystackInitializeResponse

router = APIRouter()

async def get_celebration_service(session: AsyncSession = Depends(get_session)) -> CelebrationService:
    return CelebrationService(session)

@router.get("/check-slug", response_model=SlugAvailabilityResponse)
async def check_slug(
    slug: str = Query(..., min_length=3, max_length=40),
    service: CelebrationService = Depends(get_celebration_service)
):
    """Check if a slug is available for use."""
    available = await service.check_slug_availability(slug)
    return SlugAvailabilityResponse(available=available)

@router.post("/", response_model=CelebrationPageResponse, status_code=status.HTTP_201_CREATED)
async def create_celebration(
    data: CelebrationPageCreate,
    current_user: User = Depends(get_current_user),
    service: CelebrationService = Depends(get_celebration_service)
):
    """Create a new celebration page."""
    return await service.create_celebration_page(current_user.id, data)

@router.get("/{slug}", response_model=CelebrationPageResponse)
async def get_celebration(
    slug: str,
    service: CelebrationService = Depends(get_celebration_service)
):
    """Public endpoint to get celebration page data."""
    return await service.get_celebration_by_slug(slug)

@router.post("/{celebration_id}/initialize-payment", response_model=PaystackInitializeResponse)
async def initialize_payment(
    celebration_id: UUID,
    request: PaystackInitializeRequest,
    current_user: User = Depends(get_current_user),
    service: CelebrationService = Depends(get_celebration_service)
):
    """Initialize Paystack payment for a celebration page."""
    return await service.initialize_payment(
        celebration_id=celebration_id,
        user_id=current_user.id,
        email=request.email,
        callback_url=request.callback_url
    )

@router.get("/", response_model=CelebrationPageListResponse)
async def get_user_celebrations(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: CelebrationService = Depends(get_celebration_service)
):
    """Get all celebration pages created by the current user."""
    items, total = await service.get_user_celebrations(current_user.id, page, page_size)
    return CelebrationPageListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )
