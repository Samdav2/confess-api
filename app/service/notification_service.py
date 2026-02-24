from typing import Optional, List
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.notification import Notification, NotificationType
from app.repo.notification import NotificationRepository


class NotificationService:
    async def create_notification(
        self,
        session: AsyncSession,
        user_id: UUID,
        notification_type: str,
        title: str,
        content: str,
        reference_id: Optional[UUID] = None,
        reference_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            content=content,
            reference_id=reference_id,
            reference_type=reference_type,
            metadata_=metadata,
        )
        repo = NotificationRepository(session)
        return await repo.create(notification)

    async def get_user_notifications(
        self,
        session: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        notification_type: Optional[str] = None,
        is_read: Optional[bool] = None,
    ) -> tuple[List[Notification], int]:
        """Get paginated notifications for a user."""
        repo = NotificationRepository(session)
        return await repo.get_by_user_id(
            user_id=user_id,
            skip=skip,
            limit=limit,
            notification_type=notification_type,
            is_read=is_read,
        )

    async def get_unread_count(self, session: AsyncSession, user_id: UUID) -> int:
        """Get unread notification count for a user."""
        repo = NotificationRepository(session)
        return await repo.get_unread_count(user_id)

    async def mark_as_read(
        self, session: AsyncSession, notification_id: UUID, user_id: UUID
    ) -> Optional[Notification]:
        """Mark a notification as read (with ownership check)."""
        repo = NotificationRepository(session)
        notification = await repo.get_by_id(notification_id)
        if not notification or notification.user_id != user_id:
            return None
        return await repo.mark_as_read(notification_id)

    async def mark_all_as_read(self, session: AsyncSession, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        repo = NotificationRepository(session)
        return await repo.mark_all_as_read(user_id)

    async def delete_notification(
        self, session: AsyncSession, notification_id: UUID, user_id: UUID
    ) -> bool:
        """Delete a notification (with ownership check)."""
        repo = NotificationRepository(session)
        notification = await repo.get_by_id(notification_id)
        if not notification or notification.user_id != user_id:
            return False
        return await repo.delete(notification_id)


notification_service = NotificationService()
