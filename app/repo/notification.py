from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlmodel import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, notification: Notification) -> Notification:
        """Create a new notification."""
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Get a notification by ID."""
        statement = select(Notification).where(Notification.id == notification_id)
        result = await self.session.exec(statement)
        return result.first()

    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None,
    ) -> tuple[List[Notification], int]:
        """Get notifications for a user with pagination and optional filters."""
        statement = select(Notification).where(Notification.user_id == user_id)

        if notification_type:
            statement = statement.where(Notification.type == notification_type)
        if is_read is not None:
            statement = statement.where(Notification.is_read == is_read)

        # Count total
        count_stmt = select(Notification).where(Notification.user_id == user_id)
        if notification_type:
            count_stmt = count_stmt.where(Notification.type == notification_type)
        if is_read is not None:
            count_stmt = count_stmt.where(Notification.is_read == is_read)
        count_result = await self.session.exec(count_stmt)
        total = len(count_result.all())

        # Paginated results
        statement = statement.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.exec(statement)
        return result.all(), total

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get the number of unread notifications for a user."""
        statement = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await self.session.exec(statement)
        return len(result.all())

    async def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """Mark a single notification as read."""
        notification = await self.get_by_id(notification_id)
        if not notification:
            return None

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications for a user as read. Returns count updated."""
        statement = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        result = await self.session.exec(statement)
        notifications = result.all()

        now = datetime.now(timezone.utc)
        for n in notifications:
            n.is_read = True
            n.read_at = now
            self.session.add(n)

        await self.session.commit()
        return len(notifications)

    async def delete(self, notification_id: UUID) -> bool:
        """Delete a notification."""
        notification = await self.get_by_id(notification_id)
        if not notification:
            return False

        await self.session.delete(notification)
        await self.session.commit()
        return True
