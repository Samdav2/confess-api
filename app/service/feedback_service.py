from sqlalchemy.ext.asyncio import AsyncSession
from app.repo.feedback_repo import FeedbackRepository
from app.schemas.feedback import FeedbackCreate
from app.models.feedback import Feedback

class FeedbackService:
    @staticmethod
    async def create_feedback(session: AsyncSession, feedback_in: FeedbackCreate, user_id: str, name: str) -> Feedback:
        repo = FeedbackRepository(session)
        return await repo.create_feedback(feedback_in, user_id, name)
