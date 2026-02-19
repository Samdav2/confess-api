from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from app.db.sessions import get_session
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.confess import AnonymousLink, AnonymousMessage
from app.schemas.confess import (
    AnonymousLinkCreateRequest,
    AnonymousLinkResponse,
    AnonymousMessageCreateRequest,
    AnonymousMessageResponse
)
from app.service.confess_service import confess_service

router = APIRouter()

@router.post("/links", response_model=AnonymousLinkResponse)
async def create_confession_link(
    request: AnonymousLinkCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    return await confess_service.create_link(session, current_user.id, request)

@router.get("/links/{slug}", response_model=AnonymousLinkResponse)
async def get_confession_link(
    slug: str,
    session: AsyncSession = Depends(get_session)
):
    link = await confess_service.get_link_by_slug(session, slug)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found or expired")
    return link

@router.post("/links/{slug}/extend", response_model=AnonymousLinkResponse)
async def extend_link_expiry(
    slug: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    link = await confess_service.get_link_by_slug(session, slug)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return await confess_service.extend_link_expiry(session, link.id)

@router.post("/links/{slug}/messages", response_model=AnonymousMessageResponse)
async def submit_message(
    slug: str,
    request: AnonymousMessageCreateRequest,
    req: Request,
    session: AsyncSession = Depends(get_session)
):
    # Get IP address and User-Agent
    client_host = req.client.host
    if "x-forwarded-for" in req.headers:
        client_host = req.headers["x-forwarded-for"].split(",")[0]

    user_agent = req.headers.get("user-agent")

    return await confess_service.submit_message(
        session=session,
        slug=slug,
        request=request,
        ip_address=client_host,
        user_agent=user_agent,
        latitude=request.latitude,
        longitude=request.longitude
    )

@router.get("/links/{slug}/messages", response_model=List[AnonymousMessageResponse])
async def get_messages(
    slug: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    link = await confess_service.get_link_by_slug(session, slug)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these messages")

    messages = await confess_service.get_messages(session, link.id)

    # Masking logic
    response_messages = []
    for msg in messages:
        msg_data = msg.model_dump()
        if not msg.is_hint_unlocked:
            msg_data["hint"] = "Locked - Pay ₦200 to view"
        if not msg.is_sender_clue_unlocked:
            msg_data["ip_address"] = None
            msg_data["latitude"] = None
            msg_data["longitude"] = None
            msg_data["user_agent"] = None
            msg_data["network_info"] = None
        response_messages.append(msg_data)

    return response_messages

# Paid features - For MVP, these endpoints just trigger the unlock.
# In a real payment flow, you might verify a transaction reference here.
@router.post("/messages/{message_id}/unlock-hint", response_model=AnonymousMessageResponse)
async def unlock_hint(
    message_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Verify ownership
    message = await session.get(AnonymousMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    link = await session.get(AnonymousLink, message.link_id)
    if link.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized")

    return await confess_service.unlock_hint(session, message_id)

@router.post("/messages/{message_id}/unlock-clue", response_model=AnonymousMessageResponse)
async def unlock_clue(
    message_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Verify ownership
    message = await session.get(AnonymousMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    link = await session.get(AnonymousLink, message.link_id)
    if link.user_id != current_user.id:
         raise HTTPException(status_code=403, detail="Not authorized")

    return await confess_service.unlock_clue(session, message_id)
