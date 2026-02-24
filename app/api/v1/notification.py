from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.sessions import get_session
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    MarkReadRequest,
)
from app.service.notification_service import notification_service

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, description="Filter by notification type"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get current user's notifications with pagination and optional filters."""
    notifications, total = await notification_service.get_user_notifications(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        notification_type=type,
        is_read=is_read,
    )
    unread_count = await notification_service.get_unread_count(session, current_user.id)

    return NotificationListResponse(
        total=total,
        unread_count=unread_count,
        notifications=notifications,
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get the number of unread notifications."""
    count = await notification_service.get_unread_count(session, current_user.id)
    return {"unread_count": count}


@router.put("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Mark all notifications as read for the current user."""
    count = await notification_service.mark_all_as_read(session, current_user.id)
    return {"message": f"Marked {count} notifications as read", "count": count}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Mark a single notification as read."""
    notification = await notification_service.mark_as_read(
        session, notification_id, current_user.id
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return notification


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a notification."""
    deleted = await notification_service.delete_notification(
        session, notification_id, current_user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return {"message": "Notification deleted"}
