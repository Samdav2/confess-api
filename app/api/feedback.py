from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sessions import get_session
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.service.feedback_service import FeedbackService

feedback_router = APIRouter()

@feedback_router.post("", response_model=FeedbackResponse)
async def create_feedback(
    feedback_in: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new feedback.
    """
    try:
        feedback = await FeedbackService.create_feedback(
            session,
            feedback_in,
            user_id=current_user.id,
            name=current_user.username
        )
        return feedback
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
