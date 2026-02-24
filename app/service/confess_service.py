from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status
import secrets

from app.models.confess import AnonymousLink, AnonymousMessage
from app.schemas.confess import AnonymousLinkCreateRequest, AnonymousMessageCreateRequest
from app.service.notification_service import notification_service

class ConfessService:
    async def create_link(
        self, session: AsyncSession, user_id: UUID, request: AnonymousLinkCreateRequest
    ) -> AnonymousLink:
        # Generate a unique slug
        while True:
            slug = secrets.token_urlsafe(8)
            existing = await session.exec(select(AnonymousLink).where(AnonymousLink.slug == slug))
            if not existing.first():
                break

        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)

        link = AnonymousLink(
            user_id=user_id,
            slug=slug,
            header_text=request.header_text,
            theme_color=request.theme_color,
            expires_at=expires_at
        )
        session.add(link)
        await session.commit()
        await session.refresh(link)
        return link

    async def get_link_by_slug(self, session: AsyncSession, slug: str) -> Optional[AnonymousLink]:
        statement = select(AnonymousLink).where(AnonymousLink.slug == slug)
        result = await session.exec(statement)
        link = result.first()

        if not link:
            return None

        # Check expiry
        if link.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            link.is_active = False
            session.add(link)
            await session.commit()
            return None # Or return link with is_active=False handling in router

        return link

    async def extend_link_expiry(self, session: AsyncSession, link_id: UUID) -> AnonymousLink:
        link = await session.get(AnonymousLink, link_id)
        if not link:
            raise HTTPException(status_code=404, detail="Link not found")

        if link.is_extended:
             raise HTTPException(status_code=400, detail="Link has already been extended")

        # Extend by 24 hours
        link.expires_at += timedelta(hours=24)
        link.is_extended = True
        if not link.is_active and link.expires_at > datetime.now(timezone.utc).replace(tzinfo=None):
            link.is_active = True

        session.add(link)
        await session.commit()
        await session.refresh(link)
        return link

    async def submit_message(
        self,
        session: AsyncSession,
        slug: str,
        request: AnonymousMessageCreateRequest,
        ip_address: str,
        user_agent: str = None,
        latitude: float = None,
        longitude: float = None
    ) -> AnonymousMessage:
        link = await self.get_link_by_slug(session, slug)
        if not link or not link.is_active:
             raise HTTPException(status_code=404, detail="Link not found or expired")

        message = AnonymousMessage(
            link_id=link.id,
            type=request.type,
            content=request.content,
            hint=request.hint,
            ip_address=ip_address,
            user_agent=user_agent,
            network_info=self._parse_device_info(user_agent),
            latitude=latitude,
            longitude=longitude
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)

        # Create notification for the link owner
        try:
            await notification_service.create_notification(
                session=session,
                user_id=link.user_id,
                notification_type="anonymous_message",
                title="New anonymous message! 💌",
                content="Someone sent a message to your anonymous link.",
                reference_id=message.id,
                reference_type="anonymous_message",
                metadata={"link_slug": slug},
            )
        except Exception:
            # Don't fail the message submission if notification creation fails
            pass

        return message

    async def get_user_links(self, session: AsyncSession, user_id: UUID) -> List[AnonymousLink]:
        statement = (
            select(AnonymousLink)
            .where(AnonymousLink.user_id == user_id)
            .order_by(AnonymousLink.created_at.desc())
        )
        results = await session.exec(statement)
        return results.all()

    async def get_messages(self, session: AsyncSession, link_id: UUID) -> List[AnonymousMessage]:
        statement = select(AnonymousMessage).where(AnonymousMessage.link_id == link_id).order_by(AnonymousMessage.created_at.desc())
        results = await session.exec(statement)
        messages = results.all()

        # In a real app, you might want to return schemas here or handle masking in the response model logic.
        # But for now, we'll return the objects and handle masking in the response schema/service return.
        # For simplicity in this service, we just return the messages.
        return messages

    async def unlock_hint(self, session: AsyncSession, message_id: UUID) -> AnonymousMessage:
        message = await session.get(AnonymousMessage, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        message.is_hint_unlocked = True
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message

    async def unlock_clue(self, session: AsyncSession, message_id: UUID) -> AnonymousMessage:
        message = await session.get(AnonymousMessage, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        message.is_sender_clue_unlocked = True
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message

    def _parse_device_info(self, user_agent: str) -> str:
        if not user_agent:
            return "Unknown Device"

        ua = user_agent.lower()
        if "iphone" in ua:
             return "iPhone / iOS"
        elif "android" in ua:
             return "Android Device"
        elif "windows" in ua:
             return "Windows PC"
        elif "macintosh" in ua:
             return "Mac"
        return "Mobile/Desktop"

confess_service = ConfessService()
