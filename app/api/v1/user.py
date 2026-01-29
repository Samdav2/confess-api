from app.service.user import create_user_service
from app.db.sessions import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, APIRouter, BackgroundTasks
from app.schemas.user import UserCreate, UserResponse
from app.dependencies.email_service import email_service
from app.service.auth import generate_verification_code, store_verification_code

router = APIRouter()

@router.post("/create")
async def create_user(
        new_user: UserCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_session)
) -> UserResponse:
    """
    Create a new user account and send welcome + verification emails.

    :param new_user: User registration data
    :param background_tasks: Background task queue for emails
    :param db: Database session
    """
    user_obj = await create_user_service(db=db, new_user=new_user)

    # Generate and store verification code
    verification_code = generate_verification_code()
    store_verification_code(
        email=user_obj.email,
        code=verification_code,
        user_id=str(user_obj.id)
    )

    email_service.send_user_welcome_email(
        background_tasks=background_tasks,
        email_to=user_obj.email,
        name=user_obj.username,
    )

    email_service.send_email_verification(
        background_tasks=background_tasks,
        email_to=user_obj.email,
        name=user_obj.username,
        verification_code=verification_code
    )

    return user_obj
