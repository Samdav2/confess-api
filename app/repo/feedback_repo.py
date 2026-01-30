from sqlalchemy.ext.asyncio import AsyncSession
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate

class FeedbackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_feedback(self, feedback_in: FeedbackCreate, user_id: str, name: str) -> Feedback:
        feedback = Feedback(
            **feedback_in.dict(),
            user_id=user_id,
            name=name
        )
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)
        return feedback
