from app.repo.waitlist import create_waitlist_repo
from sqlmodel.ext.asyncio.session import  AsyncSession
from app.schemas.waitlist import WaitlistCreate, Waitlist


async def create_waitlist_service(db: AsyncSession, waitlist: WaitlistCreate) -> Waitlist:
    waitlist = await create_waitlist_repo(db=db, waitlist=waitlist)
    return waitlist