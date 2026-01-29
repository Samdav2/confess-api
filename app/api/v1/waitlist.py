from app.service.waitlist import create_waitlist_service
from app.db.sessions import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, APIRouter, BackgroundTasks
from app.schemas.waitlist import WaitlistCreate
from app.dependencies.email_service import email_service

router = APIRouter(tags=["waitlist"])

@router.post("/create")
async def create_waitlist(
    waitlist: WaitlistCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    :param waitlist:
    :param background_tasks:
    :param db:
    """
    waitlist_obj = await create_waitlist_service(db=db, waitlist=waitlist)

    email_service.send_waitlist_email(
        background_tasks=background_tasks,
        email_to=waitlist_obj.email,
        name="User"
    )

    return waitlist_obj
