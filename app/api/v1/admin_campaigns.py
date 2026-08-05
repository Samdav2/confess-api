from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from app.db.sessions import get_session
from app.dependencies.auth import get_current_admin
from app.models.admin import Admin
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignSendRequest,
)
from app.service.campaign import campaign_service

router = APIRouter()


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: CampaignCreate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    campaign = await campaign_service.create_campaign(
        session=session, data=request, admin_id=current_admin.id
    )
    return campaign


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    items, total = await campaign_service.list_campaigns(
        session=session, skip=skip, limit=limit
    )
    return CampaignListResponse(total=total, items=items)


@router.get("/recipient-count")
async def get_recipient_count(
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    count = await campaign_service.get_recipient_count(session=session)
    return {"total_verified_users": count}


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    campaign = await campaign_service.get_campaign(
        session=session, campaign_id=campaign_id
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    request: CampaignUpdate,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    campaign = await campaign_service.update_campaign(
        session=session, campaign_id=campaign_id, data=request
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    deleted = await campaign_service.delete_campaign(
        session=session, campaign_id=campaign_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )


@router.post("/{campaign_id}/send", response_model=CampaignResponse)
async def send_campaign(
    campaign_id: UUID,
    request: CampaignSendRequest,
    background_tasks: BackgroundTasks,
    current_admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Set confirm=true to send the campaign",
        )

    campaign = await campaign_service.send_campaign(
        session=session,
        campaign_id=campaign_id,
        background_tasks=background_tasks,
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign
